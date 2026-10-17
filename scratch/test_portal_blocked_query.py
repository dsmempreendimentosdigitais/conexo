import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Query blocked orders in 2026 from Portal de Vendas ('pedidos' table)
sql = """
SELECT 
    COUNT(*) OVER() AS total_pedidos_geral,
    SUM(p.valor_total) OVER() AS valor_total_geral,
    p.numero AS totvs_order_code,
    c.razao_social AS cliente_nome,
    r.nome AS representante_nome,
    p.created_at::date AS data_pedido,
    p.valor_total,
    p.status
FROM pedidos p
LEFT JOIN clientes c ON c.id = p.cliente_id
LEFT JOIN representantes r ON r.codigo = p.representante_codigo
WHERE p.status = 'Bloqueado'
  AND p.valor_total > 0
  AND p.created_at::date >= '2026-01-01'
ORDER BY p.created_at DESC
LIMIT 50
"""

res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
data = res.data or []
print(f"Total blocked orders in Portal (2026): {len(data)}")
if data:
    print(f"Header Total Pedidos: {data[0].get('total_pedidos_geral')} | Valor Total: R$ {float(data[0].get('valor_total_geral') or 0):,.2f}")
    print("\nSample blocked orders:")
    for r in data[:15]:
        print(f"Code: {r.get('totvs_order_code'):15} | Client: {str(r.get('cliente_nome'))[:30]:30} | Value: R$ {float(r.get('valor_total') or 0):10,.2f} | Date: {r.get('data_pedido')}")
