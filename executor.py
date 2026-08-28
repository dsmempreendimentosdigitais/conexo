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

    # Consulta de Estoque de Pronto-Entrega
    if intent == "conexo_consulta_estoque":
        produto = params.get("produto", "").strip()
        cor = params.get("cor", "").strip()
        
        where_clauses = []
        if produto:
            terms = [t for t in produto.lower().split() if len(t) > 2]
            for term in terms:
                where_clauses.append(f"LOWER(descricao) LIKE '%{term}%'")
        if cor:
            terms = [t for t in cor.lower().split() if len(t) > 1]
            for term in terms:
                where_clauses.append(f"(LOWER(cor) LIKE '%{term}%' OR LOWER(descricao) LIKE '%{term}%' OR cor_codigo = '{term}')")
                
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        sql = f"SELECT cod_produto, descricao, cor, cor_codigo, quantidade_disponivel, quantidade_reservada, categoria, unidade FROM estoque_pe WHERE {where_sql} ORDER BY quantidade_disponivel DESC LIMIT 20"
        
        resp = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        return resp.data

    # Consulta geral dinêmica (Text-to-SQL)
    if intent == "conexo_consulta_geral":
        if ctx and ctx.get("perfil") != "gestor":
            raise ValueError("Apenas gestores podem realizar consultas personalizadas no banco de dados.")
        sql = params.get("sql", "")
        if sql:
            sql = sql.strip().rstrip(";")
        resp = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        return resp.data

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
