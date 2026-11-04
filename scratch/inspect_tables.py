import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

# Check all tables with 'item' or 'pedido' in name
q = """
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' AND (table_name LIKE '%pedid%' OR table_name LIKE '%item%')
"""

try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": q}).execute().data
    print("TABLES:")
    for r in res:
        print(f"  {r['table_name']}")
except Exception as e:
    print("Error:", e)
