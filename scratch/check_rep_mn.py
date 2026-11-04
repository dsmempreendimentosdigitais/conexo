import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

q = "SELECT * FROM representantes WHERE codigo = '3071' OR nome ILIKE '%M.N%' OR nome ILIKE '%Michele%'"
try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": q}).execute().data
    print(json.dumps(res, indent=2, ensure_ascii=False))
except Exception as e:
    print(e)
