import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

query = """
SELECT e.cod_produto, e.descricao, e.cor, e.cor_codigo, e.quantidade_disponivel, e.quantidade_reservada, e.estoque_1
FROM estoque_pe e 
WHERE e.descricao ILIKE '%Tricoline Paris%' AND (e.cor ILIKE '%Marinho%' OR e.cor_codigo = '96')
"""

try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": query}).execute().data
    print("ESTOQUE_PE RESULTS:")
    print(json.dumps(res, indent=2, ensure_ascii=False))
except Exception as e:
    print("Error:", e)
