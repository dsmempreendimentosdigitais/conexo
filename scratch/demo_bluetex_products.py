import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# 1. Orders for Blue Tex in progress (all products)
sql_all_inprogress = """
SELECT totvs_order_code, cliente_nome, status, data_pedido::date, valor_total
FROM pedidos_totvs
WHERE cliente_nome ILIKE '%blue tex%'
  AND status NOT IN ('Canceled', 'Attended')
ORDER BY data_pedido DESC
"""
res1 = supabase.rpc("conexo_executar_leitura", {"query_str": sql_all_inprogress}).execute()
print(f"1. Pedidos do cliente Blue Tex EM ANDAMENTO (todos os produtos): {len(res1.data or [])} pedidos encontrados!")
for r in (res1.data or [])[:5]:
    print(r)

# 2. Orders for Blue Tex in progress (only ESTAMPADOS)
sql_estampados_inprogress = """
SELECT totvs_order_code, cliente_nome, status, data_pedido::date, valor_total
FROM pedidos_totvs
WHERE cliente_nome ILIKE '%blue tex%'
  AND status NOT IN ('Canceled', 'Attended')
  AND items_json::text ILIKE '%estamp%'
ORDER BY data_pedido DESC
"""
res2 = supabase.rpc("conexo_executar_leitura", {"query_str": sql_estampados_inprogress}).execute()
print(f"\n2. Pedidos do cliente Blue Tex EM ANDAMENTO (apenas ESTAMPADOS): {len(res2.data or [])} pedidos encontrados!")
