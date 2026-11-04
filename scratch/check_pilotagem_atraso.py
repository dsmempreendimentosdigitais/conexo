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
  AND p.status NOT IN ('Attended', 'Canceled')
  AND p.previsao_faturamento < '2026-10-30'
ORDER BY p.previsao_faturamento ASC
"""

try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": q}).execute().data
    print(f"TOTAL ORDERS WITH LOTE PIL IN PROGRESS & ATRASADO: {len(res)}")
    print(json.dumps(res, indent=2, ensure_ascii=False))
except Exception as e:
    print(e)
