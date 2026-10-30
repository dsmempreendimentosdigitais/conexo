import sys, os
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

try:
    admin_auth = supabase.auth.admin
    print("Admin auth object:", admin_auth)
    print("Methods:", [m for m in dir(admin_auth) if not m.startswith("_")])
except Exception as e:
    print("Error admin auth:", e)
