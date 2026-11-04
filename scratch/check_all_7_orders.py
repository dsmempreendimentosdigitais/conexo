import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

order_numbers = ['36499', '36588', '37019', '37065', '37087', '37151', '37249']

q_totvs = f"""
SELECT totvs_order_code, status, data_pedido, previsao_faturamento, valor_total,
       items_json
FROM pedidos_totvs
WHERE totvs_order_code IN ({','.join([f"'{x}'" for x in order_numbers])})
"""

q_portal = f"""
SELECT id, numero, status, tipo_pedido, data_previsao_faturamento, valor_total, observacoes, payload_totvs
FROM pedidos
WHERE numero IN ({','.join([f"'{x}'" for x in order_numbers])})
"""

try:
    r_totvs = supabase.rpc("conexo_executar_leitura", {"query_str": q_totvs}).execute().data
    print(f"FOUND IN TOTVS: {len(r_totvs)}")
    for r in r_totvs:
        print(f"TOTVS #{r['totvs_order_code']} - Status: {r['status']} - Prev: {r['previsao_faturamento']}")

    r_portal = supabase.rpc("conexo_executar_leitura", {"query_str": q_portal}).execute().data
    print(f"\nFOUND IN PORTAL: {len(r_portal)}")
    for r in r_portal:
        print(f"PORTAL #{r['numero']} (ID {r['id']}) - Status: {r['status']} - Prev: {r['data_previsao_faturamento']}")
        # Look for 'PIL' or 'pilotagem' in payload_totvs or observacoes or items
        obs = r.get('observacoes') or ''
        payload = r.get('payload_totvs') or {}
        print(f"  Obs: {obs[:80]}...")
        print(f"  Payload batchOrder: {payload.get('batchOrder')}")
        if 'items' in payload:
            for it in payload['items']:
                print(f"    Item batchOrder: {it.get('batchOrder')} | desc: {it.get('productDescription')} | ref: {it.get('_missingProductRef')}")
except Exception as e:
    print("Error:", e)
