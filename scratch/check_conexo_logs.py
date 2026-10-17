import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Fetch recent logs from conexo_logs
sql = """
SELECT id, pergunta, intent, parametros, sucesso, created_at
FROM conexo_logs
ORDER BY id DESC
LIMIT 20
"""

res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
print("Recent logs from conexo_logs:")
for log in res.data:
    print(f"ID: {log.get('id')} | Success: {log.get('sucesso')} | Question: {log.get('pergunta')}")
    print(f"   Params: {log.get('parametros')}")
    print("-" * 60)
