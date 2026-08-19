from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# intents que NÃO chamam banco (tratadas no fluxo)
NAO_DB = {"fora_de_escopo", "pedir_esclarecimento"}

# intents que existem como RPC no Supabase
RPCS = {
    "conexo_vendas_periodo",
    "conexo_comparativo_mes",
    "conexo_comparativo_ano",
    "conexo_ranking_vendedores",
    "conexo_vendedores_abaixo_meta",
    "conexo_top_produtos",
    "conexo_top_clientes",
    "conexo_clientes_inativos",
    "conexo_vendas_regiao",
    "conexo_top_cores",
    "conexo_relatorio_periodo",
}

# RPCs que suportam filtro por representante (vendedor vê só o dele)
RPCS_COM_REP = {
    "conexo_ranking_vendedores",
    "conexo_vendas_periodo",
    "conexo_top_clientes",
    "conexo_top_produtos",
    "conexo_vendas_regiao",
    "conexo_top_cores",
}


def executar(intent: str, params: dict, ctx: dict | None = None):
    """
    Executa a intent. ctx contém tenant_id e rep do token (multi-tenant).
    """
    # Inteligência de mercado tem caminho próprio
    if intent == "conexo_inteligencia_mercado":
        from mercado.motor import analisar_mercado
        return analisar_mercado(params, ctx or {})

    if intent not in RPCS:
        raise ValueError(f"Intent '{intent}' não é uma RPC válida.")

    params = dict(params)

    # Multi-tenant: injeta tenant e rep do TOKEN (nunca do usuário)
    if ctx:
        params["p_tenant"] = ctx["tenant_id"]
        if intent in RPCS_COM_REP:
            params["p_rep"] = ctx.get("rep")  # None = gestor (vê tudo)

    resp = supabase.rpc(intent, params).execute()
    return resp.data
