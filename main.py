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
from admin_router import router as admin_router

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

# Registra o painel administrativo master
app.include_router(admin_router)

client_oa = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL, max_retries=1)


# ─────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────

class Turno(BaseModel):
    role: str       # "user" | "conexo"
    conteudo: str

class PerguntaIn(BaseModel):
    pergunta: str = Field(..., min_length=2, max_length=4000)
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

    try:
        intent, params = rotear(pergunta, usuario, historico)
    except Exception as e:
        error_msg = "⚠️ Ops! O assistente está temporariamente sobrecarregado (limite de requisições do Gemini atingido). Por favor, aguarde alguns segundos e envie novamente."
        if "quota" in str(e).lower() or "limit" in str(e).lower() or "429" in str(e):
            error_msg = "⚠️ Limite de requisições (Rate Limit 429) excedido no Gemini. Por favor, aguarde 15 a 30 segundos e envie a mensagem novamente."
        def erro_roteamento():
            yield f"data: {json.dumps({'tipo':'texto','delta':error_msg})}\n\n"
            yield f"data: {json.dumps({'tipo':'fim'})}\n\n"
        return StreamingResponse(erro_roteamento(), media_type="text/event-stream")

    if intent in ("fora_de_escopo", "pedir_esclarecimento"):
        texto = params.get("pergunta_ao_usuario") or (
            "Posso ajudar com vendas, clientes, produtos, vendedores, metas e mercado."
        )
        def simples():
            yield f"data: {json.dumps({'tipo':'texto','delta':texto})}\n\n"
            yield f"data: {json.dumps({'tipo':'fim'})}\n\n"
        return StreamingResponse(simples(), media_type="text/event-stream")

    try:
        dados = executar(intent, params, ctx)
        log_consulta(usuario, pergunta, intent, params, True)
    except Exception as e:
        error_msg = f"⚠️ Erro ao consultar os dados no banco de dados: {e}"
        def erro_execucao():
            yield f"data: {json.dumps({'tipo':'texto','delta':error_msg})}\n\n"
            yield f"data: {json.dumps({'tipo':'fim'})}\n\n"
        return StreamingResponse(erro_execucao(), media_type="text/event-stream")

    def gerar():
        yield f"data: {json.dumps({'tipo':'dados','intent':intent,'dados':dados}, default=str)}\n\n"

        # Se não houver dados, formata com contexto de filtros e regras de proatividade
        dados_para_prompt = dados
        if not dados:
            dados_para_prompt = {
                "FILTROS_APLICADOS_NA_CONSULTA_SQL": params,
                "TOTAL_REGISTROS_GERAL_DA_BASE": 0,
                "REGISTROS_EXIBIDOS_NA_TABELA": 0,
                "SOMA_TOTAL_EXATA_DO_BANCO": {},
                "LISTA_REGISTROS": []
            }

        if intent == "conexo_inteligencia_mercado" and isinstance(dados, dict):
            try:
                texto = formatar(pergunta, intent, dados)
            except Exception as e:
                texto = f"⚠️ Erro ao estruturar relatório de mercado: {e}"
            yield f"data: {json.dumps({'tipo':'texto','delta':texto})}\n\n"
            yield f"data: {json.dumps({'tipo':'fim'})}\n\n"
            return

        # Calcula soma exata de colunas numéricas para garantir 100% de consistência com a tabela
        dados_para_prompt = dados
        if isinstance(dados, list) and len(dados) > 0:
          first = dados[0]
          total_registros_geral = first.get("total_pedidos_geral") or first.get("total_registros_geral") or len(dados)
          
          val_keys = [k for k in first.keys() if any(x in k.lower() for x in ["valor", "faturamento", "total", "metr", "quantidade", "qtd"])]
          totais_calculados = {}
          for k in val_keys:
            if k in ["total_pedidos_geral", "total_registros_geral"]:
              continue
            if "geral" in k.lower():
              totais_calculados[k] = float(first.get(k) or 0)
            else:
              chave_geral = f"{k}_geral"
              if chave_geral in first:
                totais_calculados[k] = float(first.get(chave_geral) or 0)
              else:
                totais_calculados[k] = sum(float(r.get(k) or 0) for r in dados if isinstance(r.get(k), (int, float, str)) and str(r.get(k)).replace('.','',1).replace('-','',1).isdigit())
          
          dados_para_prompt = {
            "FILTROS_APLICADOS_NA_CONSULTA_SQL": params,
            "TOTAL_REGISTROS_GERAL_DA_BASE": int(total_registros_geral),
            "REGISTROS_EXIBIDOS_NA_TABELA": len(dados),
            "SOMA_TOTAL_EXATA_DO_BANCO": totais_calculados,
            "LISTA_REGISTROS": dados
          }

        prompt = FORMATTER_SYSTEM.format(
            empresa=config.EMPRESA, pergunta=pergunta, intent=intent,
            dados=json.dumps(dados_para_prompt, ensure_ascii=False, default=str),
        )
        import time
        stream = None
        for tentativa in range(3):
            try:
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
                break
            except Exception as e:
                if tentativa < 2 and any(k in str(e).lower() for k in ["429", "quota", "rate", "limit", "resourceexhausted"]):
                    time.sleep(2.0 * (tentativa + 1))
                    continue
                error_msg = "\n\n⚠️ Erro ao formatar a análise de resposta (Gemini temporariamente indisponível). Por favor, tente novamente em instantes."
                if "quota" in str(e).lower() or "limit" in str(e).lower() or "429" in str(e) or "resourceexhausted" in str(e).lower():
                    error_msg = "\n\n⚠️ Limite de requisições excedido no Gemini (Plano Gratuito). Para uso corporativo e apresentações sem interrupção, recomenda-se ativar o plano pago Pay-As-You-Go no Google AI Studio (custo médio de ~R$ 15 a R$ 30/mês)."
                yield f"data: {json.dumps({'tipo':'texto','delta':error_msg})}\n\n"
                break
            
        yield f"data: {json.dumps({'tipo':'fim'})}\n\n"

    return StreamingResponse(gerar(), media_type="text/event-stream")


# ─────────────────────────────────────────────────
# Transcrição de áudio (Whisper)
# ─────────────────────────────────────────────────

def _detectar_mimetype_audio(filename: str, content_type: str | None) -> str:
    fn = filename.lower()
    ct = (content_type or "").lower()
    if "webm" in fn or "webm" in ct:
        return "audio/webm"
    if "mp4" in fn or "m4a" in fn or "aac" in fn or "mp4" in ct or "m4a" in ct:
        return "audio/mp4"
    if "wav" in fn or "wav" in ct:
        return "audio/wav"
    if "ogg" in fn or "ogg" in ct:
        return "audio/ogg"
    if "mp3" in fn or "mpeg" in ct:
        return "audio/mp3"
    return "audio/webm"

@app.post("/conexo/transcrever")
async def transcrever(
    audio: UploadFile = File(...),
    ctx: dict = Depends(get_contexto),
):
    try:
        conteudo = await audio.read()
        filename = audio.filename or "fala.webm"
        if not filename.endswith((".webm", ".m4a", ".mp4", ".wav", ".ogg", ".mp3")):
            filename += ".webm"

        content_type = _detectar_mimetype_audio(filename, audio.content_type)

        if config.IS_GEMINI:
            import base64
            import httpx as requests  # httpx já está no requirements; 'requests' não está instalado no servidor

            b64_audio = base64.b64encode(conteudo).decode("utf-8")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={config.OPENAI_API_KEY}"
            payload = {
                "systemInstruction": {
                    "parts": [{
                        "text": "Você é um transcritor estrito de fala para texto (Speech-to-Text). Sua função é transcrever com total fidelidade as palavras faladas no áudio em português. NUNCA responda à pergunta, NUNCA gere saudações, NUNCA converse. Se não houver fala humana inteligível no áudio (apenas silêncio, estalos ou ruído ambiente), retorne exatamente vazio."
                    }]
                },
                "contents": [{
                    "parts": [
                        {"inline_data": {"mime_type": content_type, "data": b64_audio}},
                        {"text": "Transcreva o que foi falado no áudio:"}
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.0,
                    "thinkingConfig": {"thinkingBudget": 0}
                }
            }
            resp = requests.post(url, json=payload, timeout=25)
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Erro no serviço de áudio: {resp.text}")
            
            data = resp.json()
            candidates = data.get("candidates", [])
            texto = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    texto = parts[0].get("text", "").strip()
            
            # Limpa eventuais marcadores ou prefixos que o modelo possa gerar
            for prefixo in ["transcrição:", "áudio:", "texto:", "fala:"]:
                if texto.lower().startswith(prefixo):
                    texto = texto[len(prefixo):].strip()
            return {"texto": texto}
        else:
            resp = client_oa.audio.transcriptions.create(
                model="whisper-1",
                file=(filename, conteudo, content_type),
                language="pt",
            )
            return {"texto": resp.text}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar transcrição de áudio: {str(e)}")


# ─────────────────────────────────────────────────
# Síntese de voz (TTS) — voz masculina profissional
# ─────────────────────────────────────────────────

class FalaIn(BaseModel):
    texto: str = Field(..., max_length=6000)


def _pcm_para_wav(pcm: bytes, sample_rate: int = 24000, canais: int = 1, bits: int = 16) -> bytes:
    import struct
    byte_rate = sample_rate * canais * bits // 8
    block_align = canais * bits // 8
    header = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
    header += b"fmt " + struct.pack("<IHHIIHH", 16, 1, canais, sample_rate, byte_rate, block_align, bits)
    header += b"data" + struct.pack("<I", len(pcm))
    return header + pcm


@app.post("/conexo/falar")
def falar(body: FalaIn, ctx: dict = Depends(get_contexto)):
    from fastapi.responses import Response
    texto = (body.texto or "").strip()
    if not texto:
        raise HTTPException(status_code=400, detail="Texto vazio")
    try:
        if config.IS_GEMINI:
            import base64
            import httpx
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={config.OPENAI_API_KEY}"
            payload = {
                "contents": [{"parts": [{
                    "text": "Fale estritamente em português do Brasil (pt-BR), com sotaque brasileiro natural e paulista, sem chiar e sem nenhum sotaque de Portugal. O tom é de um executivo comercial sênior: masculino, calmo, firme, seguro e profissional:\n\n" + texto
                }]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Fenrir"}}},
                },
            }
            resp = httpx.post(url, json=payload, timeout=60)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Erro no serviço de voz: {resp.text[:300]}")
            parts = resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
            dado = next((p.get("inlineData") or p.get("inline_data") for p in parts if p.get("inlineData") or p.get("inline_data")), None)
            if not dado:
                raise HTTPException(status_code=502, detail="Serviço de voz não retornou áudio")
            pcm = base64.b64decode(dado["data"])
            return Response(content=_pcm_para_wav(pcm), media_type="audio/wav")
        else:
            audio = client_oa.audio.speech.create(model="tts-1", voice="onyx", input=texto)
            return Response(content=audio.content, media_type="audio/mpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar voz: {str(e)}")


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
# Configurações do Gestor: Minha Empresa, Suporte e Senha
# ─────────────────────────────────────────────────

class SuporteIn(BaseModel):
    assunto: str
    categoria: str = "Geral"  # Duvida | Erro | Integracao | Financeiro
    mensagem: str

class AlterarSenhaIn(BaseModel):
    nova_senha: str

@app.get("/conexo/minha-empresa")
def get_minha_empresa(ctx: dict = Depends(get_contexto)):
    tenant_id = ctx.get("tenant_id")
    if not tenant_id:
        raise HTTPException(400, "Usuário não vinculado a uma empresa.")
    
    t_res = supabase.table("tenants").select("*").eq("id", tenant_id).single().execute()
    if not t_res.data:
        raise HTTPException(404, "Empresa não encontrada.")
    t = t_res.data

    users_res = supabase.table("conexo_usuarios").select("id, ativo").eq("tenant_id", tenant_id).execute()
    total_users = len(users_res.data or [])

    conns = t.get("conectores") or {}
    total_conns_ativos = sum(1 for c in conns.values() if isinstance(c, dict) and c.get("ativo"))

    return {
        "tenant_id": t["id"],
        "nome": t.get("nome"),
        "nome_fantasia": t.get("nome_fantasia") or t.get("nome"),
        "cnpj": t.get("cnpj"),
        "plano": t.get("plano") or "Enterprise",
        "valor_mensal": t.get("valor_mensal") or 3500.0,
        "dia_vencimento": t.get("dia_vencimento") or 10,
        "status_pagamento": t.get("status_pagamento") or "em_dia",
        "total_usuarios": total_users,
        "total_conectores_ativos": total_conns_ativos,
        "contrato": t.get("contrato") or {},
        "usuario_logado": {
            "email": ctx.get("email"),
            "perfil": ctx.get("perfil")
        }
    }

@app.post("/conexo/suporte")
def abrir_suporte(body: SuporteIn, ctx: dict = Depends(get_contexto)):
    import secrets
    import datetime
    protocolo = f"SUP-{datetime.date.today().strftime('%Y%m%d')}-{secrets.token_hex(2).upper()}"
    
    try:
        supabase.table("conexo_logs").insert({
            "usuario": ctx.get("email"),
            "pergunta": f"[SUPORTE {protocolo}] {body.assunto}",
            "intent": "suporte_cliente",
            "parametros": {
                "protocolo": protocolo,
                "categoria": body.categoria,
                "mensagem": body.mensagem,
                "tenant_id": ctx.get("tenant_id")
            },
            "sucesso": True
        }).execute()
    except Exception as e:
        print("Aviso ao registrar log de suporte:", e)

    return {
        "sucesso": True,
        "protocolo": protocolo,
        "mensagem": f"Solicitação recebida com sucesso! Protocolo: {protocolo}. A equipe técnica da DSM Empreendimentos Digitais entrará em contato."
    }

@app.post("/conexo/alterar-senha")
def alterar_minha_senha(body: AlterarSenhaIn, ctx: dict = Depends(get_contexto)):
    if len(body.nova_senha) < 6:
        raise HTTPException(400, "A nova senha deve ter no mínimo 6 caracteres.")
    
    email = ctx.get("email")
    try:
        res_u = supabase.table("conexo_usuarios").select("auth_user_id, id").eq("email", email).single().execute()
        uid = res_u.data.get("auth_user_id") or res_u.data.get("id")
        supabase.auth.admin.update_user_by_id(uid, {"password": body.nova_senha})
        return {"sucesso": True, "mensagem": "Senha alterada com sucesso!"}
    except Exception as e:
        raise HTTPException(500, f"Erro ao atualizar senha: {str(e)}")


# ─────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "CONEXO API", "version": "2.0"}
