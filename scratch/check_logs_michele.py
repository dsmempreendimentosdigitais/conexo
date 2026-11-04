import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

q = "SELECT id, pergunta, intent, parametros, created_at FROM conexo_logs WHERE id >= 239 ORDER BY id ASC"
try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": q}).execute().data
    print(json.dumps(res, indent=2, ensure_ascii=False))
except Exception as e:
    print(e)
