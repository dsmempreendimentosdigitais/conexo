import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Check if table 'pedidos' exists and what columns/data it has
try:
    res_pedidos = supabase.table('pedidos').select('*').limit(10).execute()
    print(f"=== TABLE 'pedidos' (Portal de Vendas) ===")
    print("Count:", len(res_pedidos.data))
    if res_pedidos.data:
        print("Sample row keys:", res_pedidos.data[0].keys())
        print("Sample rows:")
        for r in res_pedidos.data[:5]:
            print(f"Code: {r.get('code') or r.get('pedido_code') or r.get('id')} | Status: {r.get('status')} | Total: {r.get('total_value') or r.get('valor_total')} | Date: {r.get('created_at') or r.get('data_pedido')}")
except Exception as e:
    print("Error querying 'pedidos':", e)

# Check status values in 'pedidos_totvs'
try:
    sql_totvs = """
    SELECT status, status_forca_vendas, COUNT(*), SUM(valor_total)
    FROM pedidos_totvs
    WHERE data_pedido::date >= '2026-01-01'
    GROUP BY status, status_forca_vendas
    """
    res_totvs = supabase.rpc("conexo_executar_leitura", {"query_str": sql_totvs}).execute()
    print("\n=== Status breakdown in 'pedidos_totvs' (2026) ===")
    for r in (res_totvs.data or []):
        print(r)
except Exception as e:
    print("Error querying 'pedidos_totvs':", e)
