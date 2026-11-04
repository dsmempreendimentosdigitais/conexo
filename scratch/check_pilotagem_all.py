import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

q = """
SELECT 
    p.totvs_order_code,
    p.cliente_nome,
    p.representante_codigo,
    p.representante_nome,
    p.status,
    p.status_forca_vendas,
    p.lote_pedido,
    p.data_pedido,
    p.previsao_faturamento,
    p.valor_total
FROM pedidos_totvs p
WHERE (p.lote_pedido ILIKE '%PIL%' OR p.lote_pedido ILIKE '%PILOT%')
"""

try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": q}).execute().data
    print(f"TOTAL ORDERS WITH LOTE_PEDIDO LIKE PIL: {len(res)}")
    print(json.dumps(res, indent=2, ensure_ascii=False))
except Exception as e:
    print(e)
