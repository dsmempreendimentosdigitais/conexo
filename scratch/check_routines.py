import sys, os
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

res = supabase.rpc("conexo_executar_leitura", {
    "query_str": "SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public'"
}).execute().data
print("ROUTINES:")
for r in res:
    print("-", r.get("routine_name"))
