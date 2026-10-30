import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

query = """
SELECT 
    COUNT(*) as total_rows,
    COUNT(NULLIF(quantidade_disponivel, 0)) as rows_with_disp,
    COUNT(NULLIF(quantidade_reservada, 0)) as rows_with_res,
    SUM(quantidade_disponivel) as sum_disp,
    SUM(quantidade_reservada) as sum_res
FROM estoque_pe
"""

try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": query}).execute().data
    print("ESTOQUE_PE STATS:")
    print(json.dumps(res, indent=2))
except Exception as e:
    print("Error:", e)
