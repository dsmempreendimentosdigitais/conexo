import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

sql = """
SELECT p.parameter_name, p.data_type, p.parameter_mode
FROM information_schema.parameters p
JOIN information_schema.routines r ON r.specific_name = p.specific_name
WHERE r.routine_name = 'exec_sql'
"""

res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
print("exec_sql parameters:", res.data)
