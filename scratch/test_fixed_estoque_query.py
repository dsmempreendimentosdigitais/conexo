import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

query = """
SELECT 
    e.cod_produto, 
    e.descricao, 
    e.cor, 
    e.cor_codigo, 
    ROUND(COALESCE(e.quantidade_disponivel, 0)::numeric, 1) AS quantidade_disponivel, 
    ROUND(COALESCE(e.quantidade_reservada, 0)::numeric, 1) AS quantidade_reservada, 
    ROUND(GREATEST(COALESCE(e.quantidade_disponivel, 0) + COALESCE(e.quantidade_reservada, 0), COALESCE(e.estoque_1, 0))::numeric, 1) AS estoque_fisico, 
    e.categoria, 
    e.unidade, 
    e.hex_color 
FROM estoque_pe e
WHERE e.descricao ILIKE '%Tricoline Paris%' AND (e.cor ILIKE '%Marinho%' OR e.cor_codigo = '960')
ORDER BY quantidade_disponivel DESC LIMIT 30
"""

try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": query}).execute().data
    print("NEW QUERY RESULT:")
    print(json.dumps(res, indent=2, ensure_ascii=False))
except Exception as e:
    print("Error:", e)
