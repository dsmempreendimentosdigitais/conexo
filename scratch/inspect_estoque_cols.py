import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

query = """
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'estoque_pe'
"""

try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": query}).execute().data
    print("COLUMNS:")
    for r in res:
        print(f"  {r['column_name']} ({r['data_type']})")
except Exception as e:
    print("Error:", e)
