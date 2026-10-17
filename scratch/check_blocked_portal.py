import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Check all statuses in 'pedidos' table (Portal)
try:
    sql = """
    SELECT status, COUNT(*), SUM(valor_total)
    FROM pedidos
    GROUP BY status
    """
    res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
    print("=== Statuses in 'pedidos' (Portal) ===")
    for r in (res.data or []):
        print(r)
except Exception as e:
    print("Error querying status in 'pedidos':", e)

# Check blocked orders in 'pedidos' (Portal)
try:
    sql_blocked = """
    SELECT p.id, p.numero, p.status, p.valor_total, p.created_at::date, c.razao_social AS cliente_nome, r.nome AS representante_nome
    FROM pedidos p
    LEFT JOIN clientes c ON c.id = p.cliente_id
    LEFT JOIN representantes r ON r.codigo = p.representante_codigo
    WHERE p.status ILIKE '%bloquead%'
    ORDER BY p.created_at DESC
    """
    res_blocked = supabase.rpc("conexo_executar_leitura", {"query_str": sql_blocked}).execute()
    print("\n=== Blocked Orders in 'pedidos' (Portal) ===")
    print("Count:", len(res_blocked.data or []))
    for r in (res_blocked.data or []):
        print(r)
except Exception as e:
    print("Error querying blocked in 'pedidos':", e)
