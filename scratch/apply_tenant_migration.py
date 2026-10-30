import sys, os
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

ddl = """
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS nome_fantasia TEXT;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS plano TEXT DEFAULT 'Enterprise';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS valor_mensal NUMERIC DEFAULT 3500.00;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS dia_vencimento INTEGER DEFAULT 10;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS status_pagamento TEXT DEFAULT 'em_dia';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS conectores JSONB DEFAULT '{}'::jsonb;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS logo_url TEXT;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS cor_primaria TEXT DEFAULT '#38bdf8';
"""

try:
    res = supabase.rpc("exec_sql", {"query": ddl}).execute()
    print("DDL success:", res.data)
except Exception as e:
    print("DDL error:", e)

cols = supabase.rpc("conexo_executar_leitura", {
    "query_str": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tenants'"
}).execute().data
print("NEW TENANTS COLS:")
for c in cols:
    print("-", c["column_name"], c["data_type"])
