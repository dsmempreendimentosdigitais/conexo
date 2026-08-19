import json
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from openai import OpenAI

from config import config
from router import rotear
from executor import executar, supabase, NAO_DB
from formatter import formatar
from logger import log_consulta
from auth import get_contexto
from prompts import FORMATTER_SYSTEM
from onboarding.rotas import router as onboarding_router

app = FastAPI(
    title="CONEXO API",
    version="2.0",
    description="Assistente de inteligência comercial — conexo.dev",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://conexo.dev",
        "https://www.conexo.dev",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra o router de onboarding (admin-only)
app.include_router(onboarding_router)

client_oa = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)


# ─────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────

class Turno(BaseModel):
    role: str       # "user" | "conexo"
    conteudo: str

class PerguntaIn(BaseModel):
    pergunta: str = Field(..., min_length=2, max_length=500)
    historico: list[Turno] = Field(default_factory=list)

class RespostaOut(BaseModel):
    tipo: str               # "analise" | "esclarecimento" | "fora_escopo"
    conteudo: str
    intent: str | None = None
    dados: object | None = None

class CadastroIn(BaseModel):
    cnpj:  str
    email: str
    senha: str
    setor: str | None = None


# ─────────────────────────────────────────────────
# Pergunta — resposta JSON completa
# ─────────────────────────────────────────────────

@app.post("/conexo/perguntar", response_model=RespostaOut)
def perguntar(body: PerguntaIn, ctx: dict = Depends(get_contexto)):
    pergunta  = body.pergunta.strip()
    usuario   = ctx["email"]
    historico = [t.model_dump() for t in body.historico]

    try:
        intent, params = rotear(pergunta, usuario, historico)
    except Exception as e:
        raise HTTPException(502, f"Falha no roteador: {e}")

    if intent == "fora_de_escopo":
        log_consulta(usuario, pergunta, intent, params, True)
        return RespostaOut(
            tipo="fora_escopo",
            conteudo=(
                "Ainda não sei responder isso. Posso ajudar com "
                "vendas, faturamento, clientes, produtos, vendedores, metas e mercado."
            ),
            intent=intent,
        )

    if intent == "pedir_esclarecimento":
        log_consulta(usuario, pergunta, intent, params, True)
        return RespostaOut(
            tipo="esclarecimento",
            conteudo=params.get("pergunta_ao_usuario", "Qual período você quer analisar?"),
            intent=intent,
        )

    try:
        dados = executar(intent, params, ctx)
    except Exception as e:
        log_consulta(usuario, pergunta, intent, params, False)
        raise HTTPException(500, f"Erro ao consultar dados: {e}")

    log_consulta(usuario, pergunta, intent, params, True)

    try:
        texto = formatar(pergunta, intent, dados)
    except Exception:
        texto = "Consegui os dados, mas falhei ao formatar a análise."

    return RespostaOut(tipo="analise", conteudo=texto, intent=intent, dados=dados)


# ─────────────────────────────────────────────────
# Pergunta com streaming (SSE)
# ─────────────────────────────────────────────────

@app.post("/conexo/perguntar-stream")
def perguntar_stream(body: PerguntaIn, ctx: dict = Depends(get_contexto)):
    pergunta  = body.pergunta.strip()
    usuario   = ctx["email"]
    historico = [t.model_dump() for t in body.historico]

    intent, params = rotear(pergunta, usuario, historico)

    if intent in ("fora_de_escopo", "pedir_esclarecimento"):
        texto = params.get("pergunta_ao_usuario") or (
            "Posso ajudar com vendas, clientes, produtos, vendedores, metas e mercado."
        )
        def simples():
            yield f"data: {json.dumps({'tipo':'texto','delta':texto})}\n\n"
            yield f"data: {json.dumps({'tipo':'fim'})}\n\n"
        return StreamingResponse(simples(), media_type="text/event-stream")

    dados = executar(intent, params, ctx)
    log_consulta(usuario, pergunta, intent, params, True)

    def gerar():
        yield f"data: {json.dumps({'tipo':'dados','intent':intent,'dados':dados}, default=str)}\n\n"

        if not dados:
            yield f"data: {json.dumps({'tipo':'texto','delta':'Não encontrei registros para esse período.'})}\n\n"
            yield f"data: {json.dumps({'tipo':'fim'})}\n\n"
            return

        if intent == "conexo_inteligencia_mercado" and isinstance(dados, dict):
            texto = formatar(pergunta, intent, dados)
            yield f"data: {json.dumps({'tipo':'texto','delta':texto})}\n\n"
            yield f"data: {json.dumps({'tipo':'fim'})}\n\n"
            return

        prompt = FORMATTER_SYSTEM.format(
            empresa=config.EMPRESA, pergunta=pergunta, intent=intent,
            dados=json.dumps(dados, ensure_ascii=False, default=str),
        )
        stream = client_oa.chat.completions.create(
            model=config.MODEL_FORMATTER,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield f"data: {json.dumps({'tipo':'texto','delta':delta})}\n\n"
        yield f"data: {json.dumps({'tipo':'fim'})}\n\n"

    return StreamingResponse(gerar(), media_type="text/event-stream")


# ─────────────────────────────────────────────────
# Transcrição de áudio (Whisper)
# ─────────────────────────────────────────────────

@app.post("/conexo/transcrever")
async def transcrever(
    audio: UploadFile = File(...),
    ctx: dict = Depends(get_contexto),
):
    conteudo = await audio.read()
    resp = client_oa.audio.transcriptions.create(
        model="whisper-1",
        file=(audio.filename, conteudo, audio.content_type),
        language="pt",
    )
    return {"texto": resp.text}


# ─────────────────────────────────────────────────
# Alertas
# ─────────────────────────────────────────────────

@app.get("/conexo/alertas")
def listar_alertas(ctx: dict = Depends(get_contexto)):
    r = (
        supabase.table("conexo_alertas")
        .select("*")
        .eq("tenant_id", ctx["tenant_id"])
        .eq("lido", False)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    return {"alertas": r.data}


@app.patch("/conexo/alertas/{alerta_id}/lido")
def marcar_lido(alerta_id: int, ctx: dict = Depends(get_contexto)):
    supabase.table("conexo_alertas").update({"lido": True}).eq("id", alerta_id).execute()
    return {"ok": True}


# ─────────────────────────────────────────────────
# Cadastro de usuário
# ─────────────────────────────────────────────────

@app.post("/conexo/cadastro")
def cadastrar(body: CadastroIn):
    t = (
        supabase.table("tenants")
        .select("id, ativo")
        .eq("cnpj", body.cnpj)
        .single()
        .execute()
    ).data
    if not t or not t["ativo"]:
        raise HTTPException(
            403, "CNPJ sem contrato ativo. Fale com o comercial CONEXO."
        )

    try:
        auth_resp = supabase.auth.sign_up({"email": body.email, "password": body.senha})
    except Exception:
        raise HTTPException(400, "E-mail já cadastrado ou senha inválida.")

    supabase.table("conexo_usuarios").insert({
        "auth_user_id": auth_resp.user.id,
        "tenant_id":    t["id"],
        "email":        body.email,
        "setor":        body.setor,
        "perfil":       "gestor",
    }).execute()

    return {"status": "ok", "mensagem": "Cadastro criado. Confirme seu e-mail para ativar."}


# ─────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "CONEXO API", "version": "2.0"}
