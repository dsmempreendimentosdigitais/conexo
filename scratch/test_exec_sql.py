import sys, os
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

try:
    res = supabase.rpc("exec_sql", {"sql": "SELECT 1 as test"}).execute().data
    print("exec_sql test:", res)
except Exception as e:
    print("exec_sql error:", e)
