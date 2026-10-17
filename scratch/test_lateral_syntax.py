import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# 1. Comma LATERAL syntax (the one that might fail)
sql1 = """
SELECT p.totvs_order_code, p.cliente_nome, item->>'referenceName' as produto
FROM pedidos_totvs p, LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(p.items_json) = 'array' THEN p.items_json ELSE '[]'::jsonb END) item
WHERE p.cliente_nome ILIKE '%blue tex%'
LIMIT 5
"""

# 2. CROSS JOIN LATERAL syntax
sql2 = """
SELECT p.totvs_order_code, p.cliente_nome, item->>'referenceName' as produto
FROM pedidos_totvs p
CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(p.items_json) = 'array' THEN p.items_json ELSE '[]'::jsonb END) AS item
WHERE p.cliente_nome ILIKE '%blue tex%'
LIMIT 5
"""

# 3. What if items_json is queried using JSONB containment or ILIKE without LATERAL?
sql3 = """
SELECT p.totvs_order_code, p.cliente_nome, p.valor_total, p.status, p.data_pedido::date
FROM pedidos_totvs p
WHERE p.cliente_nome ILIKE '%blue tex%'
  AND p.items_json::text ILIKE '%estamp%'
  AND p.status NOT IN ('Canceled', 'Attended')
LIMIT 10
"""

for i, sql in enumerate([sql1, sql2, sql3], 1):
    try:
        res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        print(f"SQL {i} SUCCESS! Rows returned:", len(res.data) if res.data else 0)
    except Exception as e:
        print(f"SQL {i} ERROR:", e)
