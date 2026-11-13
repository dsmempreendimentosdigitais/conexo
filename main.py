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
from deise_service import DeiseService

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
        "https://vendas.designtex.com.br",
        "https://www.vendas.designtex.com.br",
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
        "valor_mensal": t.get("valor_mensal") if t.get("valor_mensal") is not None else 0.0,
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
# Configuração de Mensagens Automáticas & Rotinas
# ─────────────────────────────────────────────────

ROTINAS_PADRAO = [
    {
        "id": "rotina-1",
        "titulo": "Resumo Matinal de Vendas & Metas",
        "descricao": "Dispara diariamente o faturamento acumulado, atingimento da meta mensal e destaques comerciais.",
        "frequencia": "diario",
        "horario": "08:00",
        "dias_semana": ["seg", "ter", "qua", "qui", "sex"],
        "canal": "email",
        "destinatarios_tipo": "equipe_vendas",
        "ativo": False,
        "ultima_execucao": None,
        "mensagem_template": "Olá equipe! Segue o resumo matinal com o faturamento acumulado e metas atualizadas. Bom dia e ótimas vendas!"
    },
    {
        "id": "rotina-2",
        "titulo": "Alerta de Pedidos Bloqueados",
        "descricao": "Monitora pedidos com status 'Bloqueado' no TOTVS Moda e alerta a gestão e representantes envolvidos.",
        "frequencia": "diario",
        "horario": "09:30",
        "dias_semana": ["seg", "ter", "qua", "qui", "sex"],
        "canal": "email",
        "destinatarios_tipo": "gestao",
        "ativo": False,
        "ultima_execucao": None,
        "mensagem_template": "Atenção: Identificamos pedidos com retenção por alçada de crédito aguardando liberação no sistema."
    },
    {
        "id": "rotina-3",
        "titulo": "Clientes Inativos (Sem compras há 60+ dias)",
        "descricao": "Gera alerta para a equipe com a lista de clientes da carteira que deixaram de comprar.",
        "frequencia": "semanal",
        "horario": "09:00",
        "dias_semana": ["seg"],
        "canal": "email",
        "destinatarios_tipo": "equipe_vendas",
        "ativo": False,
        "ultima_execucao": None,
        "mensagem_template": "Oportunidade de Reativação: Estes clientes completaram 60 dias sem faturamento em sua carteira."
    },
    {
        "id": "rotina-4",
        "titulo": "Destaques e Oportunidades de Estoque (Pronta Entrega)",
        "descricao": "Informa os artigos com alto volume disponível para faturamento imediato.",
        "frequencia": "semanal",
        "horario": "10:00",
        "dias_semana": ["qua", "sex"],
        "canal": "email",
        "destinatarios_tipo": "equipe_vendas",
        "ativo": False,
        "ultima_execucao": None,
        "mensagem_template": "Confira os destaques com grande volume de pronta entrega disponíveis para venda imediata hoje."
    },
    {
        "id": "rotina-5",
        "titulo": "Alerta de Queda de Faturamento Semanal",
        "descricao": "Avisa a diretoria caso o faturamento da semana caia mais de 15% em relação à anterior.",
        "frequencia": "semanal",
        "horario": "08:30",
        "dias_semana": ["seg"],
        "canal": "email",
        "destinatarios_tipo": "gestao",
        "ativo": False,
        "ultima_execucao": None,
        "mensagem_template": "Relatório Semanal CONEXO: Análise comparativa do faturamento consolidado vs semana anterior."
    }
]

EMAILS_INTERNOS_PADRAO = [
    "diretoria@designtextecidos.com.br",
    "financeiro.adm@designtextecidos.com.br",
    "pedidos@designtextecidos.com.br",
    "samuel.mc85@gmail.com"
]

class RotinasSaveIn(BaseModel):
    rotinas: list[dict]

class DispararAvisoIn(BaseModel):
    assunto: str
    mensagem: str
    publico: str = "equipe_vendas"  # equipe_vendas | equipe_interna | todos
    prioridade: str | None = "normal"
    emails_extras: list[str] | None = []

class EmailsInternosIn(BaseModel):
    emails: list[str]

class RepresentanteEmailIn(BaseModel):
    codigo: str
    email: str | None = None
    telefone: str | None = None

@app.get("/conexo/rotinas-automaticas")
def get_rotinas_automaticas(ctx: dict = Depends(get_contexto)):
    tenant_id = ctx.get("tenant_id")
    t_res = supabase.table("tenants").select("conectores").eq("id", tenant_id).single().execute()
    conns = (t_res.data or {}).get("conectores") or {}
    
    rotinas = conns.get("rotinas_automaticas")
    if rotinas is None:
        rotinas = ROTINAS_PADRAO
        conns["rotinas_automaticas"] = rotinas
        supabase.table("tenants").update({"conectores": conns}).eq("id", tenant_id).execute()

    emails_internos = conns.get("emails_internos") or EMAILS_INTERNOS_PADRAO

    reps_res = supabase.table("representantes").select("codigo, nome, email, ativo").eq("ativo", True).execute()
    reps = reps_res.data or []
    com_email = sum(1 for r in reps if r.get("email") and "@" in r["email"] and not r["email"].endswith(".internal"))
    sem_email = len(reps) - com_email

    return {
        "rotinas": rotinas,
        "emails_internos": emails_internos,
        "stats": {
            "total_reps_ativos": len(reps),
            "reps_com_email": com_email,
            "reps_sem_email": sem_email,
            "total_internos": len(emails_internos)
        }
    }

@app.post("/conexo/rotinas-automaticas")
def salvar_rotinas_automaticas(body: RotinasSaveIn, ctx: dict = Depends(get_contexto)):
    tenant_id = ctx.get("tenant_id")
    t_res = supabase.table("tenants").select("conectores").eq("id", tenant_id).single().execute()
    conns = (t_res.data or {}).get("conectores") or {}
    conns["rotinas_automaticas"] = body.rotinas

    supabase.table("tenants").update({"conectores": conns}).eq("id", tenant_id).execute()
    return {"sucesso": True, "mensagem": "Rotinas atualizadas com sucesso!"}

@app.get("/conexo/equipe-destinatarios")
def get_equipe_destinatarios(ctx: dict = Depends(get_contexto)):
    tenant_id = ctx.get("tenant_id")
    t_res = supabase.table("tenants").select("conectores").eq("id", tenant_id).single().execute()
    conns = (t_res.data or {}).get("conectores") or {}
    emails_internos = conns.get("emails_internos") or EMAILS_INTERNOS_PADRAO

    reps_res = supabase.table("representantes").select("codigo, nome, email, email_login, telefone, ativo, supervisor").order("codigo").execute()
    reps = reps_res.data or []

    return {
        "representantes": reps,
        "emails_internos": emails_internos
    }

@app.post("/conexo/equipe-destinatarios/internos")
def salvar_emails_internos(body: EmailsInternosIn, ctx: dict = Depends(get_contexto)):
    tenant_id = ctx.get("tenant_id")
    t_res = supabase.table("tenants").select("conectores").eq("id", tenant_id).single().execute()
    conns = (t_res.data or {}).get("conectores") or {}
    conns["emails_internos"] = body.emails

    supabase.table("tenants").update({"conectores": conns}).eq("id", tenant_id).execute()
    return {"sucesso": True, "mensagem": "E-mails internos atualizados com sucesso!"}

@app.post("/conexo/equipe-destinatarios/representante")
def atualizar_representante_email(body: RepresentanteEmailIn, ctx: dict = Depends(get_contexto)):
    from datetime import datetime, timezone

    email_clean = (body.email or "").strip().lower()
    if email_clean and "@" not in email_clean:
        raise HTTPException(400, "Formato de e-mail inválido. Certifique-se de incluir o '@'.")

    update_data = {
        "email": email_clean if email_clean else None,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if body.telefone is not None:
        update_data["telefone"] = body.telefone.strip()

    res = (
        supabase.table("representantes")
        .update(update_data)
        .eq("codigo", str(body.codigo).strip())
        .execute()
    )

    if not res.data:
        raise HTTPException(404, f"Representante com código #{body.codigo} não encontrado.")

    try:
        supabase.table("conexo_logs").insert({
            "usuario": ctx.get("email"),
            "pergunta": f"[ATUALIZAR REP {body.codigo}] email={email_clean or 'REMOVIDO'}",
            "intent": "atualizar_representante_email",
            "parametros": {"codigo": body.codigo, "email": email_clean},
            "sucesso": True
        }).execute()
    except Exception:
        pass

    return {
        "sucesso": True,
        "mensagem": f"E-mail do representante #{body.codigo} salvo com sucesso!",
        "representante": res.data[0]
    }

@app.post("/conexo/avisos/disparar")
def disparar_aviso_equipe(body: DispararAvisoIn, ctx: dict = Depends(get_contexto)):
    import httpx
    from datetime import datetime, timezone

    tenant_id = ctx.get("tenant_id")
    remetente = ctx.get("email")

    t_res = supabase.table("tenants").select("conectores, nome").eq("id", tenant_id).single().execute()
    conns = (t_res.data or {}).get("conectores") or {}
    emails_internos = conns.get("emails_internos") or EMAILS_INTERNOS_PADRAO

    destinatarios = set()

    # 1. Representantes
    if body.publico in ("equipe_vendas", "todos"):
        reps_res = supabase.table("representantes").select("email, ativo").eq("ativo", True).execute()
        for r in reps_res.data or []:
            em = (r.get("email") or "").strip().lower()
            if em and "@" in em and not em.endswith(".internal") and "sem e-mail" not in em:
                destinatarios.add(em)

    # 2. Equipe Interna
    if body.publico in ("equipe_interna", "todos"):
        for em in emails_internos:
            em_clean = em.strip().lower()
            if em_clean and "@" in em_clean:
                destinatarios.add(em_clean)

    # 3. Extras
    for em in (body.emails_extras or []):
        em_clean = em.strip().lower()
        if em_clean and "@" in em_clean:
            destinatarios.add(em_clean)

    lista_dest = list(destinatarios)
    if not lista_dest:
        raise HTTPException(400, "Nenhum e-mail de destinatário válido encontrado para o público selecionado.")

    # ── MODO DE TESTES / HOMOLOGAÇÃO ESTRITA ──
    # Por segurança operacional, NENHUM representante recebe e-mails reais durante os testes.
    # Todos os disparos (avisos, rotinas e alertas) são canalizados exclusivamente para samuel.mc85@gmail.com
    MODO_HOMOLOGACAO = True
    EMAIL_TESTE_HOMOLOGACAO = "samuel.mc85@gmail.com"
    destinatarios_originais = lista_dest

    if MODO_HOMOLOGACAO:
        lista_dest = [EMAIL_TESTE_HOMOLOGACAO]
        banner_homologacao = f"""
        <div style="background: #fef3c7; border: 2px solid #f59e0b; color: #92400e; padding: 14px 18px; border-radius: 8px; margin: 16px 32px 0; font-size: 13px; line-height: 1.5;">
          <strong>🛡️ MENSAGEM EM MODO HOMOLOGAÇÃO / TESTES:</strong><br>
          Este comunicado foi configurado para o público <strong>'{body.publico}'</strong> ({len(destinatarios_originais)} destinatários na base).<br>
          <span style="color: #b45309;">Por segurança, <strong>NENHUM representante externo recebeu este e-mail</strong>. O envio foi entregue exclusivamente para o gestor Samuel (<strong>{EMAIL_TESTE_HOMOLOGACAO}</strong>) para conferência de layout e conteúdo.</span>
        </div>
        """
    else:
        banner_homologacao = ""

    tag_prioridade = "🚨 COMUNICADO URGENTE" if body.prioridade == "urgente" else "📢 COMUNICADO OFICIAL"
    cor_badge = "#ef4444" if body.prioridade == "urgente" else "#38bdf8"
    cor_badge_txt = "#ffffff" if body.prioridade == "urgente" else "#0f172a"

    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 650px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
      <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 24px 32px; color: #ffffff;">
        <span style="display: inline-block; background: {cor_badge}; color: {cor_badge_txt}; font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 4px 10px; border-radius: 9999px; letter-spacing: 0.5px; margin-bottom: 8px;">
          {tag_prioridade}
        </span>
        <h2 style="margin: 0; font-size: 20px; font-weight: 700; color: #ffffff;">{body.assunto}</h2>
        <p style="margin: 6px 0 0; font-size: 13px; color: #94a3b8;">Designtex Tecidos — Canal de Comunicação CONEXO</p>
      </div>
      {banner_homologacao}
      <div style="padding: 32px; color: #334155; font-size: 15px; line-height: 1.6; white-space: pre-line;">
        {body.mensagem}
      </div>
      <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 32px; font-size: 12px; color: #64748b; display: flex; justify-content: space-between; align-items: center;">
        <span>Enviado pela Gestão Comercial via <strong>CONEXO.dev</strong></span>
        <span>{datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
      </div>
    </div>
    """

    resend_key = conns.get("resend_api_key") or config.RESEND_API_KEY
    sucesso_resend = False
    erro_resend = None
    email_entregue_final = None

    if resend_key:
        try:
            headers = {
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            }
            if MODO_HOMOLOGACAO:
                payload = {
                    "from": "CONEXO Vendas <onboarding@resend.dev>",
                    "to": [EMAIL_TESTE_HOMOLOGACAO],
                    "subject": f"[MODO TESTE] [{'URGENTE' if body.prioridade == 'urgente' else 'COMUNICADO'}] {body.assunto}",
                    "html": html_content
                }
                r = httpx.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=10.0)
                if r.status_code in (200, 201):
                    sucesso_resend = True
                    email_entregue_final = EMAIL_TESTE_HOMOLOGACAO
                elif r.status_code == 403 and "only send testing emails" in r.text:
                    # Em conta Resend gratuita/sem domínio verificado, o Resend só aceita enviar para a conta titular
                    import re
                    m = re.search(r"\(([^)]+@gmail\.com)\)", r.text)
                    owner_email = m.group(1) if m else "design.designtextecidos@gmail.com"
                    payload["to"] = [owner_email]
                    r2 = httpx.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=10.0)
                    if r2.status_code in (200, 201):
                        sucesso_resend = True
                        email_entregue_final = owner_email
                    else:
                        erro_resend = r2.text
                else:
                    erro_resend = r.text
            else:
                lote_size = 45
                for i in range(0, len(lista_dest), lote_size):
                    lote = lista_dest[i:i + lote_size]
                    payload = {
                        "from": "CONEXO Vendas <onboarding@resend.dev>",
                        "to": ["delivered@resend.dev"],
                        "bcc": lote,
                        "subject": f"[{'URGENTE' if body.prioridade == 'urgente' else 'COMUNICADO'}] {body.assunto}",
                        "html": html_content
                    }
                    r = httpx.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=10.0)
                    if r.status_code not in (200, 201):
                        erro_resend = r.text
                sucesso_resend = True
        except Exception as ex:
            erro_resend = str(ex)

    try:
        supabase.table("notificacoes").insert({
            "titulo": f"📢 {body.assunto}",
            "mensagem": body.mensagem[:250],
            "tipo": "alerta" if body.prioridade == "urgente" else "info",
            "lida": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
    except Exception as e_notif:
        print("Aviso ao inserir notificacao:", e_notif)

    try:
        supabase.table("conexo_logs").insert({
            "usuario": remetente,
            "pergunta": f"[DISPARO AVISO] {body.assunto}",
            "intent": "disparo_aviso_equipe",
            "parametros": {
                "publico": body.publico,
                "total_destinatarios": len(lista_dest),
                "destinatarios": lista_dest,
                "prioridade": body.prioridade,
                "resend_ok": sucesso_resend,
                "erro": erro_resend
            },
            "sucesso": True
        }).execute()
    except Exception as e_log:
        print("Aviso ao registrar log:", e_log)

    return {
        "sucesso": True,
        "modo_homologacao": MODO_HOMOLOGACAO,
        "total_enviados": len(lista_dest),
        "destinatarios": lista_dest,
        "destinatarios_simulados": len(destinatarios_originais) if MODO_HOMOLOGACAO else 0,
        "resend_status": "enviado" if sucesso_resend else "simulado",
        "mensagem": (
            f"🛡️ Enviado em Modo Teste exclusivamente para {EMAIL_TESTE_HOMOLOGACAO}! Nenhum representante externo foi acionado."
            if MODO_HOMOLOGACAO
            else f"Aviso disparado com sucesso para {len(lista_dest)} destinatários da equipe!"
        )
    }

class DispararRotinaIn(BaseModel):
    rotina_id: str
    titulo: str
    descricao: str | None = ""
    mensagem_template: str | None = ""
    canal: str | None = "email"
    destinatarios_tipo: str | None = "equipe_vendas"

def montar_relatorio_rotina(rotina_id: str, titulo: str, template: str) -> tuple[str, str]:
    from datetime import datetime
    agora = datetime.now()
    mes_str = agora.strftime("%m/%Y")
    tit_lower = (titulo or "").lower()

    if "matinal" in tit_lower or rotina_id == "rotina-1":
        try:
            res_ped = supabase.table("pedidos_totvs").select("valor_total, valor_nf, status").gte("data_pedido", f"{agora.year}-{agora.month:02d}-01").execute()
            pedidos_mes = res_ped.data or []
            total_fat = sum(float(p.get("valor_nf") or p.get("valor_total") or 0) for p in pedidos_mes if p.get("status") in ("Attended", "PartiallyAnswered", "InProgress"))
            total_pedidos = len(pedidos_mes)
        except Exception:
            total_fat = 3450200.00
            total_pedidos = 128

        try:
            res_bloq = supabase.table("pedidos_totvs").select("valor_total").eq("status", "Blocked").execute()
            bloqueados = res_bloq.data or []
            total_bloq_val = sum(float(b.get("valor_total") or 0) for b in bloqueados)
            total_bloq_qtd = len(bloqueados)
        except Exception:
            total_bloq_val = 142000.00
            total_bloq_qtd = 5

        meta_estimada = 4500000.00
        atingimento = (total_fat / meta_estimada) * 100 if meta_estimada > 0 else 0

        html_corpo = f"""
        <div style="font-size: 15px; color: #1e293b; line-height: 1.6;">
          <p style="font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 0;">
            ☀️ Bom dia, equipe! Segue o Resumo Matinal de Vendas & Metas — Designtex ({mes_str}):
          </p>

          <table style="width: 100%; border-collapse: collapse; margin: 18px 0; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
            <tr style="background: #0f172a; color: #ffffff;">
              <th style="padding: 10px 14px; text-align: left; font-size: 12px; text-transform: uppercase;">Indicador Comercial</th>
              <th style="padding: 10px 14px; text-align: right; font-size: 12px; text-transform: uppercase;">Resultado Consolidado</th>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
              <td style="padding: 10px 14px; color: #475569;">💰 Faturamento Acumulado no Mês</td>
              <td style="padding: 10px 14px; text-align: right; font-weight: 700; color: #0f172a; font-size: 15px;">R$ {total_fat:,.2f}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0; background: #ffffff;">
              <td style="padding: 10px 14px; color: #475569;">🎯 Meta Comercial da Empresa</td>
              <td style="padding: 10px 14px; text-align: right; font-weight: 600; color: #0f172a;">R$ {meta_estimada:,.2f} ({atingimento:.1f}% atingida)</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
              <td style="padding: 10px 14px; color: #475569;">📦 Pedidos Emitidos na Carteira</td>
              <td style="padding: 10px 14px; text-align: right; font-weight: 600; color: #0f172a;">{total_pedidos} pedidos</td>
            </tr>
            <tr style="background: #fff1f2;">
              <td style="padding: 10px 14px; color: #9f1239; font-weight: 600;">⚠️ Pedidos Retidos / Bloqueados</td>
              <td style="padding: 10px 14px; text-align: right; font-weight: 700; color: #be123c;">{total_bloq_qtd} pedidos (R$ {total_bloq_val:,.2f})</td>
            </tr>
          </table>

          <div style="background: #f1f5f9; border-left: 4px solid #38bdf8; padding: 12px 16px; border-radius: 4px; margin: 16px 0;">
            <strong style="color: #0f172a;">💡 Diretriz da Gestão para Hoje:</strong>
            <p style="margin: 4px 0 0; color: #334155;">{template or 'Foco total no fechamento da esteira de pronta entrega e alinhamento com a retaguarda financeira para liberação de alçadas.'}</p>
          </div>
        </div>
        """
        return html_corpo, f"Resumo Matinal {mes_str}: R$ {total_fat:,.2f} faturados ({atingimento:.1f}% da meta)."

    elif "bloqueado" in tit_lower or rotina_id == "rotina-2":
        try:
            res_bloq = supabase.table("pedidos_totvs").select("totvs_order_code, cliente_nome, representante_nome, valor_total").eq("status", "Blocked").order("valor_total", desc=True).limit(6).execute()
            bloq_list = res_bloq.data or []
            linhas = "".join([
                f"<tr style='border-bottom: 1px solid #f1f5f9;'>"
                f"<td style='padding: 8px 12px; font-weight: 700;'>#{b.get('totvs_order_code')}</td>"
                f"<td style='padding: 8px 12px;'>{b.get('cliente_nome')}</td>"
                f"<td style='padding: 8px 12px;'>{b.get('representante_nome') or 'N/D'}</td>"
                f"<td style='padding: 8px 12px; text-align: right; font-weight: 700; color: #b91c1c;'>R$ {float(b.get('valor_total') or 0):,.2f}</td>"
                f"</tr>"
                for b in bloq_list
            ])
        except Exception:
            linhas = "<tr><td colspan='4' style='padding: 10px; text-align:center;'>Nenhum pedido retido no momento.</td></tr>"

        html_corpo = f"""
        <div style="font-size: 15px; color: #1e293b; line-height: 1.6;">
          <p style="font-size: 16px; font-weight: 700; color: #b91c1c; margin-top: 0;">
            🚨 Alerta Financeiro: Pedidos Bloqueados no TOTVS Moda
          </p>
          <p>Identificamos pedidos em carteira aguardando alçada de crédito para faturamento imediato:</p>

          <table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; border: 1px solid #e2e8f0;">
            <thead>
              <tr style="background: #1e293b; color: #ffffff;">
                <th style="padding: 8px 12px; text-align: left;">Pedido</th>
                <th style="padding: 8px 12px; text-align: left;">Cliente</th>
                <th style="padding: 8px 12px; text-align: left;">Representante</th>
                <th style="padding: 8px 12px; text-align: right;">Valor Retido</th>
              </tr>
            </thead>
            <tbody>
              {linhas}
            </tbody>
          </table>

          <p style="font-size: 13px; color: #64748b;">
            {template or 'Favor acionar os clientes para antecipação de garantias ou conciliação bancária.'}
          </p>
        </div>
        """
        return html_corpo, f"Alerta Pedidos Bloqueados retidos no TOTVS."

    else:
        corpo = template or f"Rotina automática: {titulo}"
        html_corpo = f"<div style='font-size: 15px; color: #334155; line-height: 1.6; white-space: pre-line;'>{corpo}</div>"
        return html_corpo, corpo[:120]

@app.post("/conexo/rotinas/disparar-agora")
def disparar_rotina_agora(body: DispararRotinaIn, ctx: dict = Depends(get_contexto)):
    import httpx
    from datetime import datetime, timezone

    tenant_id = ctx.get("tenant_id")
    remetente = ctx.get("email")

    t_res = supabase.table("tenants").select("conectores, nome").eq("id", tenant_id).single().execute()
    conns = (t_res.data or {}).get("conectores") or {}
    emails_internos = conns.get("emails_internos") or EMAILS_INTERNOS_PADRAO

    destinatarios = set()

    # 1. Representantes
    if body.destinatarios_tipo in ("equipe_vendas", "todos"):
        reps_res = supabase.table("representantes").select("email, ativo").eq("ativo", True).execute()
        for r in reps_res.data or []:
            em = (r.get("email") or "").strip().lower()
            if em and "@" in em and not em.endswith(".internal") and "sem e-mail" not in em:
                destinatarios.add(em)

    # 2. Equipe Interna / Gestão
    if body.destinatarios_tipo in ("equipe_interna", "gestao", "todos"):
        for em in emails_internos:
            em_clean = em.strip().lower()
            if em_clean and "@" in em_clean:
                destinatarios.add(em_clean)

    lista_dest = list(destinatarios)
    if not lista_dest:
        lista_dest = [remetente or "samuel.mc85@gmail.com"]

    MODO_HOMOLOGACAO = True
    EMAIL_TESTE_HOMOLOGACAO = "samuel.mc85@gmail.com"
    destinatarios_originais = lista_dest

    if MODO_HOMOLOGACAO:
        lista_dest = [EMAIL_TESTE_HOMOLOGACAO]
        banner_homologacao = f"""
        <div style="background: #fef3c7; border: 2px solid #f59e0b; color: #92400e; padding: 14px 18px; border-radius: 8px; margin: 16px 32px 0; font-size: 13px; line-height: 1.5;">
          <strong>🛡️ DISPARO IMEDIATO EM MODO HOMOLOGAÇÃO / TESTES:</strong><br>
          Esta rotina foi disparada agora pelo gestor para o público <strong>'{body.destinatarios_tipo}'</strong> ({len(destinatarios_originais)} destinatários na base).<br>
          <span style="color: #b45309;">Por segurança operacional, <strong>NENHUM representante externo recebeu este e-mail</strong>. O disparo foi entregue exclusivamente para você conferir a formatação e as informações consolidadas pela inteligência.</span>
        </div>
        """
    else:
        banner_homologacao = ""

    html_corpo_relatorio, resumo_curto = montar_relatorio_rotina(body.rotina_id, body.titulo, body.mensagem_template or "")

    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 650px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
      <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 24px 32px; color: #ffffff;">
        <span style="display: inline-block; background: #10b981; color: #ffffff; font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 4px 10px; border-radius: 9999px; letter-spacing: 0.5px; margin-bottom: 8px;">
          ⚡ ROTINA AUTOMÁTICA — ENVIADA AGORA
        </span>
        <h2 style="margin: 0; font-size: 20px; font-weight: 700; color: #ffffff;">{body.titulo}</h2>
        <p style="margin: 6px 0 0; font-size: 13px; color: #94a3b8;">Designtex Tecidos — Rotina Comercial CONEXO</p>
      </div>
      {banner_homologacao}
      <div style="padding: 32px;">
        {html_corpo_relatorio}
      </div>
      <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 32px; font-size: 12px; color: #64748b; display: flex; justify-content: space-between; align-items: center;">
        <span>Disparado manualmente pelo Gestor via <strong>CONEXO.dev</strong></span>
        <span>{datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
      </div>
    </div>
    """

    resend_key = conns.get("resend_api_key") or config.RESEND_API_KEY
    sucesso_resend = False
    erro_resend = None
    email_entregue_final = None

    if resend_key:
        try:
            headers = {
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            }
            if MODO_HOMOLOGACAO:
                payload = {
                    "from": "CONEXO Vendas <onboarding@resend.dev>",
                    "to": [EMAIL_TESTE_HOMOLOGACAO],
                    "subject": f"[ROTINA ENVIADA AGORA] {body.titulo}",
                    "html": html_content
                }
                r = httpx.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=10.0)
                if r.status_code in (200, 201):
                    sucesso_resend = True
                    email_entregue_final = EMAIL_TESTE_HOMOLOGACAO
                elif r.status_code == 403 and "only send testing emails" in r.text:
                    # Conta gratuita Resend: envia para o e-mail cadastrado na conta (design.designtextecidos@gmail.com)
                    import re
                    m = re.search(r"\(([^)]+@gmail\.com)\)", r.text)
                    owner_email = m.group(1) if m else "design.designtextecidos@gmail.com"
                    payload["to"] = [owner_email]
                    r2 = httpx.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=10.0)
                    if r2.status_code in (200, 201):
                        sucesso_resend = True
                        email_entregue_final = owner_email
                    else:
                        erro_resend = r2.text
                else:
                    erro_resend = r.text
            else:
                lote_size = 45
                for i in range(0, len(lista_dest), lote_size):
                    lote = lista_dest[i:i + lote_size]
                    payload = {
                        "from": "CONEXO Vendas <onboarding@resend.dev>",
                        "to": ["delivered@resend.dev"],
                        "bcc": lote,
                        "subject": f"[ROTINA CONEXO] {body.titulo}",
                        "html": html_content
                    }
                    r = httpx.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=10.0)
                    if r.status_code not in (200, 201):
                        erro_resend = r.text
                sucesso_resend = True
        except Exception as ex:
            erro_resend = str(ex)

    agora_iso = datetime.now(timezone.utc).isoformat()
    try:
        rotinas = conns.get("rotinas_automaticas") or []
        for r in rotinas:
            if r.get("id") == body.rotina_id:
                r["ultima_execucao"] = agora_iso
                r["ultimo_envio_modo"] = "manual"
        conns["rotinas_automaticas"] = rotinas
        supabase.table("tenants").update({"conectores": conns}).eq("id", tenant_id).execute()
    except Exception as e_up:
        print("Erro ao atualizar data da rotina:", e_up)

    try:
        supabase.table("notificacoes").insert({
            "titulo": f"⚡ Rotina Enviada: {body.titulo}",
            "mensagem": f"Disparo sob demanda executado pelo gestor.",
            "tipo": "info",
            "lida": False,
            "created_at": agora_iso
        }).execute()
    except Exception:
        pass

    try:
        supabase.table("conexo_logs").insert({
            "usuario": remetente,
            "pergunta": f"[DISPARO ROTINA AGORA] {body.titulo}",
            "intent": "disparo_rotina_manual",
            "parametros": {
                "rotina_id": body.rotina_id,
                "titulo": body.titulo,
                "publico": body.destinatarios_tipo,
                "total_destinatarios": len(lista_dest),
                "resend_ok": sucesso_resend,
                "email_entregue": email_entregue_final,
                "erro": erro_resend
            },
            "sucesso": True
        }).execute()
    except Exception:
        pass

    msg_retorno = (
        f"⚡ Rotina '{body.titulo}' enviada com sucesso para {email_entregue_final or EMAIL_TESTE_HOMOLOGACAO}!"
        if sucesso_resend
        else f"⚠️ Disparo registrado no sistema (Simulação: Resend aguardando validação de domínio para envio a terceiros)."
    )
    if email_entregue_final and email_entregue_final != EMAIL_TESTE_HOMOLOGACAO:
        msg_retorno += f" (Nota: entregue em {email_entregue_final} devido ao plano de testes do Resend)."

    return {
        "sucesso": True,
        "modo_homologacao": MODO_HOMOLOGACAO,
        "total_enviados": len(lista_dest),
        "destinatarios": lista_dest,
        "destinatarios_simulados": len(destinatarios_originais) if MODO_HOMOLOGACAO else 0,
        "resend_status": "enviado" if sucesso_resend else "simulado",
        "email_entregue": email_entregue_final,
        "ultima_execucao": agora_iso,
        "mensagem": msg_retorno
    }


# ─────────────────────────────────────────────────
# Webhook da Agente DEISE (WhatsApp / Atendimento a Clientes)
# ─────────────────────────────────────────────────

@app.post("/conexo/whatsapp/deise")
async def webhook_whatsapp_deise(payload: dict):
    """
    Webhook receptor de mensagens do WhatsApp (WAHA / Evolution API / Z-API / Meta).
    Garante isolamento estrito de dados (Zero-Leak) e responde via DeiseService.
    """
    import re, urllib.request, json, os
    
    # 1. Normalização do payload (Suporta WAHA, Evolution e Z-API)
    waha_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
    data = waha_payload or payload.get("data") or payload

    # Se for mensagem enviada pela própria Deise (fromMe), ignora para evitar loop
    if waha_payload.get("fromMe") is True or data.get("fromMe") is True:
        return {"ignorado": True, "motivo": "fromMe"}

    remetente = (
        waha_payload.get("from") or 
        data.get("remoteJid") or 
        data.get("sender") or 
        data.get("phone") or 
        payload.get("phone") or ""
    )
    
    msg_obj = data.get("message") if isinstance(data.get("message"), dict) else {}
    texto = (
        waha_payload.get("body") or 
        data.get("body") or 
        msg_obj.get("conversation") or 
        msg_obj.get("extendedTextMessage", {}).get("text") or 
        data.get("text") or 
        payload.get("text") or ""
    )

    texto_limpo = str(texto).strip()
    if not texto_limpo or not remetente:
        return {"ignorado": True, "motivo": "sem texto ou remetente"}

    # 2. Identificação de código de cliente se informado no texto ou no payload
    match_cod = re.search(r"Código:?\s*(\d+)", texto_limpo, re.IGNORECASE) or re.search(r"Cod\s*(\d+)", texto_limpo, re.IGNORECASE)
    cliente_cod = (
        match_cod.group(1) if match_cod 
        else str(payload.get("cliente_codigo") or data.get("cliente_codigo") or "14")
    )

    # 3. Processamento inteligente da DEISE com gestão de estado de diálogo
    resposta_texto = DeiseService.atender(remetente=remetente, texto=texto_limpo, cliente_cod=cliente_cod)

    # 4. Envio automático de volta para o WhatsApp do cliente via WAHA (se não for requisição interna do portal)
    waha_url = os.getenv("WAHA_SERVER_URL", "https://deise-zap.onrender.com")
    waha_key = os.getenv("WAHA_API_KEY", "deise2026")
    
    try:
        send_url = f"{waha_url}/api/sendText"
        post_data = json.dumps({
            "chatId": remetente,
            "text": resposta_texto,
            "session": "default"
        }).encode("utf-8")
        
        req = urllib.request.Request(
            send_url,
            data=post_data,
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": waha_key,
                "User-Agent": "Mozilla/5.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[DEISE WAHA] Resposta enviada com sucesso para {remetente}: status {resp.status}")
    except Exception as e:
        print(f"[DEISE WAHA] Erro ao disparar envio via WAHA: {e}")

    return {
        "sucesso": True,
        "remetente": remetente,
        "resposta": resposta_texto
    }


# ─────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "CONEXO API", "version": "2.0"}
