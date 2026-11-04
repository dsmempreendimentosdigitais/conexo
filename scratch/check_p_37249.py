import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

q = """
SELECT id, numero, representante_codigo 
FROM pedidos 
WHERE numero = '37249' OR id::text = '37249'
"""
try:
    r = supabase.rpc("conexo_executar_leitura", {"query_str": q}).execute().data
    print("In pedidos:", r)
except Exception as e:
    print(e)
