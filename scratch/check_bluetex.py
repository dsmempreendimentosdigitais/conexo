import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# 1. Check all clients containing 'blue' or 'tex'
sql1 = """
SELECT DISTINCT cliente_codigo, cliente_nome
FROM pedidos_totvs
WHERE cliente_nome ILIKE '%blue%' OR cliente_nome ILIKE '%tex%'
"""

res1 = supabase.rpc("conexo_executar_leitura", {"query_str": sql1}).execute()
print("Clients matching 'blue' or 'tex':")
for c in (res1.data or []):
    print(c)

# 2. Check all orders for client BLUETEX or BLUE TEX
sql2 = """
SELECT totvs_order_code, cliente_nome, status, data_pedido::date, valor_total, items_json
FROM pedidos_totvs
WHERE cliente_nome ILIKE '%blue%'
LIMIT 20
"""

res2 = supabase.rpc("conexo_executar_leitura", {"query_str": sql2}).execute()
print("\nOrders for client matching 'blue':", len(res2.data or []))
for o in (res2.data or []):
    print(f"Order: {o.get('totvs_order_code')} | Client: {o.get('cliente_nome')} | Status: {o.get('status')} | Date: {o.get('data_pedido')}")
    # inspect items in this order
    items = o.get('items_json') or []
    for it in items[:3]:
        print(f"   Item: name='{it.get('name')}', ref='{it.get('referenceName')}', color='{it.get('colorName')}'")
