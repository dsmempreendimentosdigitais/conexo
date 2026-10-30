import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import config
from supabase import create_client

sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

sql = """
WITH pedidos_unificados AS (
    SELECT
        p.id AS local_id,
        p.numero AS pedido,
        COALESCE(pt.representante_codigo, p.representante_codigo) AS rep_codigo,
        COALESCE(pt.representante_nome, r.nome, '') AS rep_nome,
        COALESCE(c.razao_social, c.nome_fantasia, pt.cliente_nome, p.payload_totvs->>'customerName', '-') AS cliente,
        COALESCE(p.tipo_pedido, '-') AS tipo,
        CASE
            WHEN p.tipo_pedido = 'OP' OR p.numero_op IS NOT NULL THEN COALESCE(p.numero_op, p.payload_totvs->>'batchOrder', NULLIF(pt.lote_pedido, 'PE'), 'OP')
            ELSE COALESCE(NULLIF(pt.lote_pedido, ''), p.payload_totvs->>'batchOrder', p.tipo_pedido, '-')
        END AS lote_pedido,
        CASE
            WHEN COALESCE(pt.status, p.status) IN ('InProgress', 'Em andamento', 'open', 'aberto', '1') THEN 'Em andamento'
            WHEN COALESCE(pt.status, p.status) IN ('Blocked', 'Bloqueado', '5') THEN 'Bloqueado'
            WHEN COALESCE(pt.status, p.status) IN ('InComposition', 'Em composição', 'Em composicao', '7') THEN 'Em composição'
            WHEN COALESCE(pt.status, p.status) IN ('Pending', 'InAnalysis', 'Em análise', 'Em analise', '8') THEN 'Em análise'
            WHEN COALESCE(pt.status, p.status) IN ('PartiallyAnswered', 'Parcialmente Atendido', '3') THEN 'Parcialmente Atendido'
            WHEN COALESCE(pt.status, p.status) IN ('Attended', 'Atendido', 'Faturado', '4') THEN 'Atendido'
            WHEN COALESCE(pt.status, p.status) IN ('Canceled', 'Cancelled', 'Cancelado', '6', '9') THEN 'Cancelado'
            ELSE COALESCE(pt.status, p.status)
        END AS status_norm,
        p.created_at::date AS data_pedido,
        COALESCE(pt.valor_total, p.valor_total, 0)::numeric AS order_valor_total,
        pt.items_json AS pt_items_json
    FROM pedidos p
    LEFT JOIN clientes c ON c.id = p.cliente_id
    LEFT JOIN representantes r ON r.codigo = p.representante_codigo
    LEFT JOIN LATERAL (
        SELECT pt2.*
        FROM pedidos_totvs pt2
        WHERE pt2.representante_codigo = p.representante_codigo
          AND (
              pt2.totvs_order_code = p.numero
              OR (p.payload_totvs->>'orderId' IS NOT NULL AND pt2.totvs_order_id = p.payload_totvs->>'orderId')
          )
        ORDER BY pt2.id DESC
        LIMIT 1
    ) pt ON true

    UNION ALL

    SELECT
        NULL::bigint AS local_id,
        pt.totvs_order_code AS pedido,
        pt.representante_codigo AS rep_codigo,
        COALESCE(pt.representante_nome, r.nome, '') AS rep_nome,
        COALESCE(pt.cliente_nome, '-') AS cliente,
        '-' AS tipo,
        COALESCE(NULLIF(pt.lote_pedido, ''), '-') AS lote_pedido,
        CASE
            WHEN pt.status IN ('InProgress', 'Em andamento', 'open', 'aberto', '1') THEN 'Em andamento'
            WHEN pt.status IN ('Blocked', 'Bloqueado', '5') THEN 'Bloqueado'
            WHEN pt.status IN ('InComposition', 'Em composição', 'Em composicao', '7') THEN 'Em composição'
            WHEN pt.status IN ('Pending', 'InAnalysis', 'Em análise', 'Em analise', '8') THEN 'Em análise'
            WHEN pt.status IN ('PartiallyAnswered', 'Parcialmente Atendido', '3') THEN 'Parcialmente Atendido'
            WHEN pt.status IN ('Attended', 'Atendido', 'Faturado', '4') THEN 'Atendido'
            WHEN pt.status IN ('Canceled', 'Cancelled', 'Cancelado', '6', '9') THEN 'Cancelado'
            ELSE pt.status
        END AS status_norm,
        pt.data_pedido::date AS data_pedido,
        COALESCE(pt.valor_total, 0)::numeric AS order_valor_total,
        pt.items_json AS pt_items_json
    FROM pedidos_totvs pt
    LEFT JOIN representantes r ON r.codigo = pt.representante_codigo
    WHERE NOT EXISTS (
        SELECT 1 FROM pedidos p
        WHERE p.representante_codigo = pt.representante_codigo
          AND (
              p.numero = pt.totvs_order_code
              OR (p.payload_totvs->>'orderId' IS NOT NULL AND p.payload_totvs->>'orderId' = pt.totvs_order_id)
          )
    )
),
pedidos_filtrados AS (
    SELECT *
    FROM pedidos_unificados
    WHERE status_norm IN ('Em andamento', 'Bloqueado', 'Em composição', 'Em análise')
      AND lote_pedido = 'EXC'
),
itens_resolvidos AS (
    SELECT
        pf.rep_codigo,
        pf.pedido,
        pf.cliente,
        pf.tipo,
        pf.lote_pedido,
        pf.status_norm AS status,
        pf.data_pedido,
        COALESCE(pi.quantidade, 0)::numeric AS metros_item,
        CASE
            WHEN COALESCE(pi.subtotal, 0) > 0 AND NOT (
                (SELECT COUNT(*) FROM pedido_itens pi2 WHERE pi2.pedido_id = pf.local_id) > 1
                AND pf.order_valor_total > 0
                AND COALESCE(pi.subtotal, 0) >= pf.order_valor_total
            ) THEN pi.subtotal::numeric
            ELSE ROUND((COALESCE(pi.quantidade, 0)::numeric * COALESCE(pi.preco_unitario, 0)::numeric), 2)
        END AS valor_item
    FROM pedidos_filtrados pf
    JOIN pedido_itens pi ON pi.pedido_id = pf.local_id

    UNION ALL

    SELECT
        pf.rep_codigo,
        pf.pedido,
        pf.cliente,
        pf.tipo,
        pf.lote_pedido,
        pf.status_norm AS status,
        pf.data_pedido,
        COALESCE((item->>'quantity')::numeric, 0) AS metros_item,
        ROUND((COALESCE((item->>'quantity')::numeric, 0) * COALESCE((item->>'price')::numeric, 0)), 2) AS valor_item
    FROM pedidos_filtrados pf
    CROSS JOIN LATERAL jsonb_array_elements(
        CASE WHEN jsonb_typeof(pf.pt_items_json) = 'array' THEN pf.pt_items_json ELSE '[]'::jsonb END
    ) AS item
    WHERE (pf.local_id IS NULL OR NOT EXISTS (SELECT 1 FROM pedido_itens pi3 WHERE pi3.pedido_id = pf.local_id))
)
SELECT 
    COUNT(DISTINCT pedido) as total_pedidos,
    ROUND(SUM(metros_item)::numeric, 1) as total_metros,
    ROUND(SUM(valor_item)::numeric, 2) as total_valor
FROM itens_resolvidos
"""

res = sb.rpc("conexo_executar_leitura", {"query_str": sql.strip()}).execute().data
print("RESULTADO EXATO DA UNIFICAÇÃO PARA LOTE 'EXC':")
print(res)
