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


import unicodedata

def desacentuar(txt: str) -> str:
    if not txt:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(txt)) if unicodedata.category(c) != "Mn"
    ).lower().strip()


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
            terms = [desacentuar(t) for t in produto.split() if len(t) >= 2]
            for term in terms:
                where_clauses.append(
                    f"(translate(lower(e.descricao), 'áàâãéèêíïóôõöúçñ', 'aaaeeeiooooucn') LIKE '%{term}%' OR lower(e.cod_produto) LIKE '%{term}%')"
                )
        if cor:
            terms = [desacentuar(t) for t in cor.split() if len(t) >= 1]
            for term in terms:
                where_clauses.append(
                    f"(translate(lower(e.cor), 'áàâãéèêíïóôõöúçñ', 'aaaeeeiooooucn') LIKE '%{term}%' OR translate(lower(e.descricao), 'áàâãéèêíïóôõöúçñ', 'aaaeeeiooooucn') LIKE '%{term}%' OR lower(e.cor_codigo) LIKE '%{term}%')"
                )
                
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        sql = f"""
        WITH reservas_vivas AS (
            SELECT 
                item->>'colorCode' as cor_codigo,
                COALESCE(SUM((item->>'quantity')::numeric), 0) as reserva_pedidos
            FROM pedidos_totvs p,
            LATERAL jsonb_array_elements(
                CASE WHEN jsonb_typeof(p.items_json) = 'array' THEN p.items_json ELSE '[]'::jsonb END
            ) item
            WHERE p.status IN ('InProgress', 'Blocked', 'InComposition')
            GROUP BY item->>'colorCode'
        )
        SELECT 
            e.cod_produto, 
            e.descricao, 
            e.cor, 
            e.cor_codigo, 
            GREATEST(0, ROUND((COALESCE(NULLIF(e.estoque_1, 0), e.quantidade_disponivel + e.quantidade_reservada, 0) - GREATEST(COALESCE(r.reserva_pedidos, 0), e.quantidade_reservada))::numeric, 1)) AS quantidade_disponivel, 
            GREATEST(COALESCE(r.reserva_pedidos, 0), e.quantidade_reservada) AS quantidade_reservada, 
            ROUND(GREATEST(COALESCE(e.estoque_1, 0), e.quantidade_disponivel + e.quantidade_reservada)::numeric, 1) AS estoque_fisico, 
            e.categoria, 
            e.unidade, 
            e.hex_color 
        FROM estoque_pe e
        LEFT JOIN reservas_vivas r ON e.cor_codigo = r.cor_codigo
        WHERE {where_sql} 
        ORDER BY quantidade_disponivel DESC LIMIT 30
        """
        
        resp = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        return resp.data

    # Consulta de Programação PCP (Produção de Tecidos)
    if intent == "conexo_consulta_programacao":
        produto = params.get("produto", "").strip()
        cor = params.get("cor", "").strip()
        
        where_clauses = []
        if produto:
            terms = [desacentuar(t) for t in produto.split() if len(t) >= 2]
            for term in terms:
                where_clauses.append(
                    f"(translate(lower(nome_tecido), 'áàâãéèêíïóôõöúçñ', 'aaaeeeiooooucn') LIKE '%{term}%' OR lower(cod_tecido) LIKE '%{term}%' OR translate(lower(tipo), 'áàâãéèêíïóôõöúçñ', 'aaaeeeiooooucn') LIKE '%{term}%')"
                )
        if cor:
            terms = [desacentuar(t) for t in cor.split() if len(t) >= 1]
            for term in terms:
                where_clauses.append(
                    f"(translate(lower(nome_cor), 'áàâãéèêíïóôõöúçñ', 'aaaeeeiooooucn') LIKE '%{term}%' OR lower(cod_cor) LIKE '%{term}%')"
                )
                
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        sql = f"SELECT op, cod_tecido, nome_tecido, cod_cor, nome_cor, quantidade_solicitada, quantidade_disponivel, previsao_faturamento, tipo FROM programacoes WHERE {where_sql} ORDER BY quantidade_solicitada DESC LIMIT 30"
        
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
