import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import config
from supabase import create_client

sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Consulta unificada de pedidos EXC
# Regra do Portal de Vendas:
# 1. pedidos_totvs onde lote_pedido = 'EXC' e status IN ('InProgress', 'Blocked')
# 2. pedidos do Portal onde tipo_pedido = 'EXC' e status IN ('Em andamento', 'Bloqueado') que ainda não estão integrados no TOTVS (pedidos locais W...)

sql = """
WITH totvs_exc AS (
    SELECT 
        totvs_order_code as numero,
        cliente_nome,
        representante_codigo,
        representante_nome,
        status,
        quantidade_total as metros,
        valor_total as valor,
        lote_pedido as lote,
        items_json
    FROM pedidos_totvs
    WHERE lote_pedido = 'EXC'
      AND status IN ('InProgress', 'Blocked')
      AND quantidade_total > 0
),
portal_exc AS (
    SELECT 
        p.numero,
        COALESCE(c.razao_social, c.nome_fantasia, 'Cliente ' || p.cliente_id::text) as cliente_nome,
        p.representante_codigo,
        r.nome as representante_nome,
        p.status,
        COALESCE(p.itens_quantidade, (SELECT sum(pi.quantidade) FROM pedido_itens pi WHERE pi.pedido_id = p.id), 0) as metros,
        p.valor_total as valor,
        p.tipo_pedido as lote,
        NULL::jsonb as items_json
    FROM pedidos p
    LEFT JOIN clientes c ON c.id = p.cliente_id
    LEFT JOIN representantes r ON r.codigo = p.representante_codigo
    WHERE p.tipo_pedido = 'EXC'
      AND p.status IN ('Em andamento', 'Bloqueado')
      AND p.numero LIKE 'W%'
      AND NOT EXISTS (
          SELECT 1 FROM pedidos_totvs pt WHERE pt.totvs_order_code = p.numero
      )
)
SELECT 
    'TOTVS ERP' as origem,
    count(*) as qtd,
    ROUND(sum(metros)::numeric, 2) as metros,
    ROUND(sum(valor)::numeric, 2) as valor
FROM totvs_exc
UNION ALL
SELECT 
    'PORTAL W...' as origem,
    count(*) as qtd,
    ROUND(sum(metros)::numeric, 2) as metros,
    ROUND(sum(valor)::numeric, 2) as valor
FROM portal_exc
UNION ALL
SELECT 
    'TOTAL GERAL UNIFICADO (EXC)' as origem,
    count(*) as qtd,
    ROUND(sum(metros)::numeric, 2) as metros,
    ROUND(sum(valor)::numeric, 2) as valor
FROM (
    SELECT metros, valor FROM totvs_exc
    UNION ALL
    SELECT metros, valor FROM portal_exc
) unificado;
"""

res = sb.rpc("conexo_executar_leitura", {"query_str": sql.strip()}).execute().data
print("=== RESULTADO DA UNIFICAÇÃO DE PEDIDOS EXC ===")
for r in res:
    print(r)
