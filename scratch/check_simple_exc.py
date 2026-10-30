import os, sys, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import config
from supabase import create_client

sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def run_query(sql):
    for i in range(3):
        try:
            return sb.rpc("conexo_executar_leitura", {"query_str": sql.strip()}).execute().data
        except Exception as e:
            print(f"Tentativa {i+1} falhou: {e}")
            time.sleep(2)
    return []

# 1. Total pedidos_totvs com lote EXC em carteira (InProgress + Blocked)
sql_totvs = """
SELECT 
    COUNT(*) as qtd,
    ROUND(SUM(quantidade_total)::numeric, 1) as metros,
    ROUND(SUM(valor_total)::numeric, 2) as valor
FROM pedidos_totvs
WHERE lote_pedido = 'EXC'
  AND status IN ('InProgress', 'Blocked')
"""
print("TOTVS EXC:")
print(run_query(sql_totvs))

# 2. Total pedidos portal com tipo EXC em carteira (Em andamento + Bloqueado)
sql_portal = """
SELECT 
    COUNT(*) as qtd,
    ROUND(SUM(valor_total)::numeric, 2) as valor
FROM pedidos
WHERE tipo_pedido = 'EXC'
  AND status IN ('Em andamento', 'Bloqueado')
"""
print("PORTAL EXC:")
print(run_query(sql_portal))
