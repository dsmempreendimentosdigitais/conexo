import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

q = """
SELECT 
    p.totvs_order_code,
    p.cliente_nome,
    p.previsao_faturamento,
    p.status,
    p.lote_pedido,
    p.valor_total
FROM pedidos_totvs p 
WHERE p.previsao_faturamento::date < '2026-10-30' 
  AND p.status NOT IN ('Attended', 'PartiallyAnswered', 'Canceled') 
  AND p.valor_total > 0 
  AND (p.lote_pedido ILIKE '%PIL%' OR p.lote_pedido ILIKE '%PILOT%')
ORDER BY p.previsao_faturamento ASC
"""

try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": q}).execute().data
    print(f"COUNT: {len(res)}")
    print(json.dumps(res, indent=2, ensure_ascii=False))
except Exception as e:
    print(e)
