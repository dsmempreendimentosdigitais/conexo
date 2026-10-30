import sys, os
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

ddl = """
ALTER TABLE estoque_pe ADD COLUMN IF NOT EXISTS custo_medio NUMERIC;
ALTER TABLE estoque_pe ADD COLUMN IF NOT EXISTS custo_aquisicao NUMERIC;
ALTER TABLE catalogo_produtos ADD COLUMN IF NOT EXISTS custo_medio NUMERIC;
ALTER TABLE precos_tabela ADD COLUMN IF NOT EXISTS custo_estimado NUMERIC;
"""

try:
    res = supabase.rpc("exec_sql", {"query": ddl}).execute()
    print("DDL success:", res.data)
except Exception as e:
    print("DDL error:", e)

cols = supabase.rpc("conexo_executar_leitura", {
    "query_str": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'estoque_pe' AND column_name LIKE '%custo%'"
}).execute().data
print("COLUNAS DE CUSTO EM ESTOQUE_PE:")
for c in cols:
    print("-", c["column_name"], c["data_type"])
