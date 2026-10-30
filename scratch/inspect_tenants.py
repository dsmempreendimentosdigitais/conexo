import sys, os
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

try:
    cols = supabase.rpc("conexo_executar_leitura", {
        "query_str": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tenants'"
    }).execute().data
    print("TENANTS COLS:", cols)
except Exception as e:
    print("Error cols:", e)

try:
    tenants = supabase.table("tenants").select("*").execute().data
    print("TENANTS ROWS:", len(tenants), tenants)
except Exception as e:
    print("Error tenants:", e)

try:
    users = supabase.table("conexo_usuarios").select("*").execute().data
    print("USUARIOS ROWS:", len(users), users)
except Exception as e:
    print("Error users:", e)
