import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

sql = """
SELECT 
    p.numero,
    p.status,
    p.valor_total,
    p.created_at::date as data_criacao,
    c.razao_social as cliente_nome,
    r.nome as representante_nome
FROM pedidos p
LEFT JOIN clientes c ON c.id = p.cliente_id
LEFT JOIN representantes r ON r.codigo = p.representante_codigo
WHERE p.status = 'Bloqueado'
ORDER BY p.created_at DESC
LIMIT 20
"""

res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
print("=== Blocked orders in 'pedidos' (Portal de Vendas) ===")
for r in (res.data or []):
    print(r)
