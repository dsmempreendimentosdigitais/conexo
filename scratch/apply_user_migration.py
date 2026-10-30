import sys, os
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

cols = supabase.rpc("conexo_executar_leitura", {
    "query_str": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'conexo_usuarios'"
}).execute().data
print("USUARIOS COLS:")
for c in cols:
    print("-", c["column_name"], c["data_type"])

ddl_user = """
ALTER TABLE conexo_usuarios ADD COLUMN IF NOT EXISTS nome TEXT;
ALTER TABLE conexo_usuarios ADD COLUMN IF NOT EXISTS telefone TEXT;
ALTER TABLE conexo_usuarios ADD COLUMN IF NOT EXISTS ultimo_login TIMESTAMPTZ;
"""
supabase.rpc("exec_sql", {"query": ddl_user}).execute()
print("USUARIOS MIGRATION APPLIED")
