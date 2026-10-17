from executor import supabase

r = supabase.rpc('conexo_executar_leitura', {
    'query_str': "SELECT codigo, nome, supervisor, meta, ativo FROM representantes WHERE nome ILIKE '%Fernandes%' OR nome ILIKE '%Andre%' OR codigo = '3019'"
}).execute()
print("Representante:", r.data)

q_pedidos = """
SELECT 
    COUNT(totvs_order_code) as total_pedidos,
    ROUND(SUM(COALESCE(valor_nf, valor_total))::numeric, 2) as total_faturado,
    MIN(data_pedido::date) as primeiro_pedido,
    MAX(data_pedido::date) as ultimo_pedido,
    COUNT(DISTINCT cliente_nome) as total_clientes
FROM pedidos_totvs
WHERE representante_codigo = '3019' OR representante_nome ILIKE '%Fernandes%'
"""
p = supabase.rpc('conexo_executar_leitura', {'query_str': q_pedidos}).execute()
print("Resumo pedidos:", p.data)

q_clientes = """
SELECT 
    cliente_nome,
    COUNT(totvs_order_code) as qtd_pedidos,
    ROUND(SUM(COALESCE(valor_nf, valor_total))::numeric, 2) as total_comprado,
    MIN(data_pedido::date) as primeiro_pedido,
    MAX(data_pedido::date) as ultimo_pedido
FROM pedidos_totvs
WHERE representante_codigo = '3019' OR representante_nome ILIKE '%Fernandes%'
GROUP BY cliente_nome
ORDER BY total_comprado DESC
LIMIT 10
"""
c = supabase.rpc('conexo_executar_leitura', {'query_str': q_clientes}).execute()
print("Top clientes:", c.data)
