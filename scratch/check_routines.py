import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

sql = """
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'public'
"""

res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
print("Public routines:", res.data)
