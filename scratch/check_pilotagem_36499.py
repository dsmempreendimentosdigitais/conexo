import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

# Check in pedidos_totvs
q1 = """
SELECT id, totvs_order_code, status, data_pedido, data_faturamento, previsao_faturamento, 
       valor_total, items_json
FROM pedidos_totvs 
WHERE totvs_order_code = '36499'
"""

# Check in pedidos (Portal de Vendas)
q2 = """
SELECT *
FROM pedidos 
WHERE numero = '36499' OR id::text = '36499' OR id::text = '41732' OR numero = '41732'
"""

print("=== CHECKING PEDIDOS_TOTVS ===")
try:
    r1 = supabase.rpc("conexo_executar_leitura", {"query_str": q1}).execute().data
    print(json.dumps(r1, indent=2, ensure_ascii=False))
except Exception as e:
    print("Error r1:", e)

print("=== CHECKING PEDIDOS (PORTAL DE VENDAS) ===")
try:
    r2 = supabase.rpc("conexo_executar_leitura", {"query_str": q2}).execute().data
    print(json.dumps(r2, indent=2, ensure_ascii=False))
except Exception as e:
    print("Error r2:", e)
