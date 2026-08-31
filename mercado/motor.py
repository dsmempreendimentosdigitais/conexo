import json
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI
from config import config
from executor import supabase, executar
from mercado.busca import buscar_web

client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)

MERCADO_SYSTEM = """Você é o Diretor Comercial e Economista Têxtil do CONEXO para a {empresa} (Designtex Indústria e Comércio de Tecidos).
Setor: Indústria Têxtil (Tecelagem de Tecidos Planos — Tricoline, Sarja, Linho, Popeline).
Insumos-chave: Fio de Algodão (penteado/cardado), Elastano, Fio de Poliéster, Viscose, Corantes, Energia e Frete.
Data de análise: {data}.

Sua missão é responder com EXTREMA INTELIGÊNCIA DE MERCADO a qualquer pergunta sobre fatores externos e internos que afetam o mercado têxtil e a tecelagem.

TEMAS DE INTELIGÊNCIA DE MERCADO COBERTOS:
1. ALGODÃO & SAFRA: Cotação Cepea/ESALQ, safra de algodão em caroço/pluma (Mato Grosso e Bahia), condições climáticas (El Niño/La Niña), qualidade de fibra (comprimento/resistência) e custo da fiação.
2. CÂMBIO & FRETE: Dólar PTAX, custo de contêineres e frete marítimo Ásia-Brasil (SCFI), taxa de frete rodoviário nacional e impacto no custo de insumos importados.
3. CONCORRÊNCIA INTERNACIONAL & CHINA: Exportação têxtil chinesa, tarifa de importação de tecidos e confecções, Shein/Shopee, Remessa Conforme e defesa comercial do setor têxtil (Abit).
4. MACROECONOMIA & TRABALHISTA: Proposta da Escala 6x1, convenções coletivas de trabalho (CCT) no polo têxtil (Americana/Santa Bárbara/Brás/Bom Retiro), inflação (IPCA), juros (Selic) e crédito para confecções.
5. REVISTAS E EDICIONAIS TÊXTEIS: Notícias Abit, Guia Jeanswear, Notícias Agrícolas, Valor Econômico, Textile World, Cepea.

REGRAS DE RESPOSTA:
- NUNCA responda que não tem dados ou que não é possível analisar. Se as notícias da busca web forem escassas, use seu amplo conhecimento de especialista do setor têxtil para construir um panorama completo, acionável e executivo.
- Relacione SEMPRE o cenário externo (algodão, dólar, China, 6x1, frete) com o impacto direto na PRECIFICAÇÃO da Designtex (custo/metro dos tecidos) e na saúde financeira das confecções clientes.
- Formate a resposta em seções executivas claras:
  📌 **Cenário & Tendências de Mercado**
  💡 **Impacto na Precificação e Custos (Designtex & Clientes)**
  🎯 **Recomendações Comerciais Acionáveis**
- Tom altamente profissional, executivo, direto e estratégico em PT-BR.
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
    Analisa cenários de mercado e macroeconomia têxtil, cruzando dados externos e internos.
    Retorna {"analise": str, "fontes": list}.
    """
    tenant_id = ctx.get("tenant_id", "")
    p = _perfil_tenant(tenant_id) if tenant_id else {}
    agora = datetime.now(ZoneInfo(config.TIMEZONE))

    assunto = params.get("assunto", "mercado textil e algodão")
    resultados = buscar_web(assunto)

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
        data=agora.strftime("%d/%m/%Y"),
    )

    user_content = f"PERGUNTA / TEMA SOLICITADO PELO GESTOR: {assunto}\n\n"
    if resultados:
        user_content += f"NOTÍCIAS E NOTAS RECENTES ENCONTRADAS NA WEB:\n{json.dumps(resultados, ensure_ascii=False)}\n\n"
    else:
        user_content += "NOTA: A busca web em tempo real não retornou itens específicos. Use seu amplo conhecimento especialista do setor têxtil brasileiro e internacional para dar um panorama completo sobre o tema.\n\n"

    if interno:
        user_content += f"DADOS INTERNOS DA DESIGNTEX (banco de dados):\n{json.dumps(interno, ensure_ascii=False, default=str)}\n\n"

    resp = client.chat.completions.create(
        model=config.MODEL_FORMATTER,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user_content},
        ],
        temperature=0.4,
    )

    return {
        "analise": resp.choices[0].message.content,
        "fontes":  resultados,
    }

