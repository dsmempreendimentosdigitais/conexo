import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from supabase import create_client

sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

query = """
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'sac_tickets'::regclass;
"""

try:
    res = sb.rpc("exec_sql", {"query": query}).execute()
    print("exec_sql:", res.data)
except Exception as e:
    print("Error:", e)
