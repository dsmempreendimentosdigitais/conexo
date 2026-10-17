import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

sql1 = """
SELECT 
    COUNT(DISTINCT p.totvs_order_code) OVER() AS total_pedidos_geral,
    SUM(p.valor_total) OVER() AS valor_total_geral,
    SUM(p.quantidade_total) OVER() AS metragem_total_geral,
    p.totvs_order_code,
    p.cliente_nome,
    p.representante_nome,
    p.data_pedido::date,
    p.valor_total,
    p.previsao_faturamento::date,
    p.status,
    item->>'referenceName' AS produto,
    item->>'colorName' AS cor,
    (item->>'quantity')::numeric AS quantidade_item
FROM pedidos_totvs p
CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(p.items_json) = 'array' THEN p.items_json ELSE '[]'::jsonb END) AS item
LEFT JOIN representantes rep ON rep.codigo = p.representante_codigo
WHERE p.cliente_nome ILIKE '%blue tex%'
  AND p.status NOT IN ('Canceled', 'Attended')
  AND (item->>'referenceName' ILIKE '%estamp%' OR item->>'name' ILIKE '%estamp%')
ORDER BY p.data_pedido DESC
LIMIT 50
""".strip().rstrip(";")

sql2 = """
SELECT 
    COUNT(*) OVER() AS total_pedidos_geral,
    SUM(p.valor_total) OVER() AS valor_total_geral,
    SUM(p.quantidade_total) OVER() AS metragem_total_geral,
    p.totvs_order_code,
    p.cliente_nome,
    p.representante_nome,
    p.data_pedido::date,
    p.valor_total,
    p.previsao_faturamento::date,
    p.status
FROM pedidos_totvs p
LEFT JOIN representantes rep ON rep.codigo = p.representante_codigo
WHERE p.cliente_nome ILIKE '%blue tex%'
  AND p.status NOT IN ('Canceled', 'Attended')
  AND p.items_json::text ILIKE '%estamp%'
ORDER BY p.data_pedido DESC
LIMIT 50
""".strip().rstrip(";")

for i, sql in enumerate([sql1, sql2], 1):
    try:
        res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        print(f"Test {i} SUCCESS! Rows:", len(res.data) if res.data else 0)
        if res.data:
            print("Sample row:", res.data[0])
    except Exception as e:
        print(f"Test {i} ERROR:", e)
