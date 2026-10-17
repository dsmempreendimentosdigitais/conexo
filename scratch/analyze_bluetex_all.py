import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Fetch ALL orders for BLUE TEX
sql = """
SELECT totvs_order_code, cliente_nome, status, data_pedido::date, data_faturamento::date, valor_total, items_json
FROM pedidos_totvs
WHERE cliente_nome ILIKE '%blue tex%'
ORDER BY data_pedido DESC
"""

res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
data = res.data or []
print(f"Total orders for BLUE TEX: {len(data)}")

statuses = {}
estampados_found = []

for o in data:
    st = o.get('status')
    statuses[st] = statuses.get(st, 0) + 1
    items = o.get('items_json') or []
    for it in items:
        name = str(it.get('name') or '')
        ref = str(it.get('referenceName') or '')
        color = str(it.get('colorName') or '')
        if 'estamp' in name.lower() or 'estamp' in ref.lower() or 'estamp' in color.lower() or 'desenho' in name.lower():
            estampados_found.append((o.get('totvs_order_code'), st, o.get('data_pedido'), name, ref, color))

print("Statuses distribution:", statuses)
print(f"Estampados found for BLUE TEX: {len(estampados_found)}")
for e in estampados_found:
    print(e)
