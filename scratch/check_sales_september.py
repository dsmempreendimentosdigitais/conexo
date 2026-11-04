import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

# Sales of the whole company in Sept 2026
q_total = """
SELECT 
    COUNT(totvs_order_code) as total_pedidos,
    ROUND(SUM(COALESCE(valor_nf, valor_total))::numeric, 2) as faturamento_total,
    ROUND(SUM(quantidade_total)::numeric, 1) as metragem_total
FROM pedidos_totvs
WHERE status IN ('Attended', 'PartiallyAnswered')
  AND nota_fiscal_data::date >= '2026-09-01' AND nota_fiscal_data::date <= '2026-09-30'
"""

# Sales of Michele (M.N - Rep 3071) in Sept 2026
q_michele = """
SELECT 
    representante_codigo,
    representante_nome,
    COUNT(totvs_order_code) as total_pedidos,
    ROUND(SUM(COALESCE(valor_nf, valor_total))::numeric, 2) as faturamento_total,
    ROUND(SUM(quantidade_total)::numeric, 1) as metragem_total
FROM pedidos_totvs
WHERE status IN ('Attended', 'PartiallyAnswered')
  AND (representante_codigo = '3071' OR representante_nome ILIKE '%M.N%')
  AND nota_fiscal_data::date >= '2026-09-01' AND nota_fiscal_data::date <= '2026-09-30'
GROUP BY representante_codigo, representante_nome
"""

try:
    r_total = supabase.rpc("conexo_executar_leitura", {"query_str": q_total}).execute().data
    print("TOTAL EMPRESA SETEMBRO 2026:")
    print(json.dumps(r_total, indent=2))

    r_michele = supabase.rpc("conexo_executar_leitura", {"query_str": q_michele}).execute().data
    print("\nMICHELE (M.N - 3071) SETEMBRO 2026:")
    print(json.dumps(r_michele, indent=2))
except Exception as e:
    print(e)
