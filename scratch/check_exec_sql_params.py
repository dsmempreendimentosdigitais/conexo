import sys, os
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

res = supabase.rpc("conexo_executar_leitura", {
    "query_str": "SELECT parameter_name, data_type FROM information_schema.parameters WHERE specific_name LIKE '%exec_sql%'"
}).execute().data
print("EXEC_SQL PARAMS:", res)
