import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

q = """
WITH pedidos_unificados AS (
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
            ELSE pt.status
        END AS status_norm,
        pt.data_pedido::date AS data_pedido,
        pt.previsao_faturamento::date AS previsao_faturamento,
        COALESCE(pt.valor_total, 0)::numeric AS order_valor_total,
        pt.items_json AS pt_items_json
    FROM pedidos_totvs pt
    LEFT JOIN representantes r ON r.codigo = pt.representante_codigo
    WHERE pt.totvs_order_code = '37249'
)
SELECT 
    pu.*,
    item->>'name' as item_name,
    item->>'quantity' as item_qty,
    item->>'price' as item_price
FROM pedidos_unificados pu
CROSS JOIN LATERAL jsonb_array_elements(
    CASE WHEN jsonb_typeof(pu.pt_items_json) = 'array' THEN pu.pt_items_json ELSE '[]'::jsonb END
) AS item
"""
try:
    r = supabase.rpc("conexo_executar_leitura", {"query_str": q}).execute().data
    print("37249 test:", len(r))
    if len(r) > 0:
        print(r[0])
except Exception as e:
    print(e)
