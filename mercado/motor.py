import json
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI
from config import config
from executor import supabase, executar
from mercado.busca import buscar_web

client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)

MERCADO_SYSTEM = """Você é o analista de mercado do CONEXO para a {empresa}.
Setor: {setor} | Nicho: {nicho} | Insumos-chave: {insumos} | Região: {regiao}.
Data atual: {data}.

Você recebe: (1) resultados de pesquisa web recentes e (2), quando houver,
DADOS INTERNOS reais da empresa (fonte da verdade do banco).

REGRAS INEGOCIÁVEIS:
- Sobre o NEGÓCIO da empresa (vendas, produtos), use APENAS os dados internos.
  Nunca invente números internos.
- Sobre o MERCADO, use apenas as fontes da pesquisa. SEMPRE cite a fonte e a
  data entre parênteses. Se a informação não tiver fonte confiável, diga que
  não encontrou dado confiável — não chute.
- Quando houver os dois, CRUZE: explique como o cenário externo se relaciona
  com o desempenho interno, e dê 1-2 recomendações acionáveis.
- Seja executivo, curto, em PT-BR. Valores em R$ 1.234,56.
- Nunca apresente dado de mercado sem fonte.
"""


def _perfil_tenant(tenant_id: str) -> dict:
    try:
        t = (
            supabase.table("tenants")
            .select("perfil_mercado")
            .eq("id", tenant_id)
            .single()
            .execute()
        )
        return t.data.get("perfil_mercado") or {}
    except Exception:
        return {}


def analisar_mercado(params: dict, ctx: dict) -> dict:
    """
    Busca dados de mercado na web e, opcionalmente, cruza com dado interno.
    Retorna {"analise": str, "fontes": list}.
    """
    tenant_id = ctx.get("tenant_id", "")
    p = _perfil_tenant(tenant_id) if tenant_id else {}
    agora = datetime.now(ZoneInfo(config.TIMEZONE))

    query = (
        f"{params['assunto']} "
        f"{p.get('nicho', '')} "
        f"{p.get('regiao_atuacao', 'Brasil')} "
        f"{agora.year}"
    ).strip()
    resultados = buscar_web(query)

    interno = None
    if params.get("cruzar_com_interno") and params.get("intent_interno") and tenant_id:
        try:
            interno = executar(
                params["intent_interno"],
                {"inicio": params.get("inicio"), "fim": params.get("fim")},
                ctx,
            )
        except Exception:
            interno = None

    system = MERCADO_SYSTEM.format(
        empresa=config.EMPRESA,
        setor=p.get("setor", "-"),
        nicho=p.get("nicho", "-"),
        insumos=", ".join(p.get("insumos_chave", [])) or "-",
        regiao=p.get("regiao_atuacao", "Brasil"),
        data=agora.strftime("%Y-%m-%d"),
    )

    user_content = (
        f"PERGUNTA: {params['assunto']}\n\n"
        f"RESULTADOS WEB:\n{json.dumps(resultados, ensure_ascii=False)}"
    )
    if interno:
        user_content += (
            f"\n\nDADOS INTERNOS (verdade do banco):\n"
            f"{json.dumps(interno, ensure_ascii=False, default=str)}"
        )

    resp = client.chat.completions.create(
        model=config.MODEL_FORMATTER,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user_content},
        ],
        temperature=0.3,
    )

    return {
        "analise": resp.choices[0].message.content,
        "fontes":  resultados,
    }
