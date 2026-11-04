import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from supabase import create_client

sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Try to query pg_constraint via RPC or execute query
try:
    sql = """
    SELECT conname, pg_get_constraintdef(c.oid) as def
    FROM pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    WHERE t.relname = 'sac_tickets';
    """
    res = sb.rpc("exec_sql", {"query": sql}).execute()
    print("exec_sql result:", res.data)
except Exception as e:
    print("Error calling exec_sql:", e)

# Also let's inspect the table sac_tickets directly
try:
    res2 = sb.table("sac_tickets").select("*").limit(5).execute()
    print("Sample sac_tickets data:", res2.data)
except Exception as e:
    print("Error querying sac_tickets:", e)
