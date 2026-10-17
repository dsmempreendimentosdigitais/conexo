import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

sql = "SELECT id, pergunta, intent, parametros, sucesso, created_at FROM conexo_logs ORDER BY id DESC LIMIT 25"

res = supabase.rpc("exec_sql", {"query": sql}).execute()
print("Raw data type:", type(res.data))
print("Raw data:", res.data)
