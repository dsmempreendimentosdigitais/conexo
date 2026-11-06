import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from supabase import create_client

sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

try:
    res = sb.table("pedidos_totvs").select("*").limit(1).execute()
    if res.data:
        print("Columns in pedidos_totvs:", list(res.data[0].keys()))
except Exception as e:
    print("Error:", e)
