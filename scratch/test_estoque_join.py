import sys
sys.path.insert(0, '.')
from executor import supabase

sql = """
WITH vendas_itens AS (
    SELECT 
        regexp_replace(COALESCE(item->>'referenceCode', ''), '[^0-9]', '', 'g') AS cod_prod,
        TRIM(COALESCE(item->>'colorCode', '')) AS cod_cor,
        MAX(COALESCE(item->>'referenceName', item->>'name')) AS nome_produto,
        MAX(COALESCE(item->>'colorName', item->>'colorCode')) AS nome_cor,
        ROUND(SUM(COALESCE((item->>'settledQuantity')::numeric, (item->>'quantity')::numeric, 0)), 1) AS metragem_vendida,
        ROUND(SUM(COALESCE((item->>'settledQuantity')::numeric, (item->>'quantity')::numeric, 0) * COALESCE((item->>'price')::numeric, 0)), 2) AS valor_vendido
    FROM pedidos_totvs p
    CROSS JOIN LATERAL jsonb_array_elements(
        CASE WHEN jsonb_typeof(p.items_json) = 'array' THEN p.items_json ELSE '[]'::jsonb END
    ) AS item
    WHERE p.status IN ('Attended', 'PartiallyAnswered')
      AND COALESCE(p.valor_nf, p.valor_total) > 0
      AND COALESCE(p.nota_fiscal_data, p.data_pedido)::date >= '2026-01-01'
    GROUP BY 1, 2
),
estoque_agrupado AS (
    SELECT 
        cod_produto,
        cor_codigo,
        MAX(descricao) AS descricao,
        MAX(cor) AS cor,
        ROUND(SUM(quantidade_disponivel)::numeric, 1) AS estoque_disponivel
    FROM estoque_pe
    GROUP BY cod_produto, cor_codigo
),
top_vendidos AS (
    SELECT 
        '1. MAIS VENDIDOS' AS categoria_analise,
        COALESCE(e.descricao, v.nome_produto) AS produto,
        COALESCE(e.cor, v.nome_cor) AS cor,
        COALESCE(e.estoque_disponivel, 0) AS estoque_atual_m,
        COALESCE(v.metragem_vendida, 0) AS vendas_metragem,
        COALESCE(v.valor_vendido, 0) AS vendas_valor
    FROM estoque_agrupado e
    FULL OUTER JOIN vendas_itens v ON e.cod_produto = v.cod_prod AND e.cor_codigo = v.cod_cor
    WHERE COALESCE(v.valor_vendido, 0) > 0
    ORDER BY vendas_valor DESC
    LIMIT 10
),
estoque_alto_venda_baixa AS (
    SELECT 
        '2. ESTOQUE ALTO / VENDA BAIXA' AS categoria_analise,
        e.descricao AS produto,
        e.cor AS cor,
        e.estoque_disponivel AS estoque_atual_m,
        COALESCE(v.metragem_vendida, 0) AS vendas_metragem,
        COALESCE(v.valor_vendido, 0) AS vendas_valor
    FROM estoque_agrupado e
    LEFT JOIN vendas_itens v ON e.cod_produto = v.cod_prod AND e.cor_codigo = v.cod_cor
    WHERE e.estoque_disponivel >= 1000
    ORDER BY e.estoque_disponivel DESC, COALESCE(v.metragem_vendida, 0) ASC
    LIMIT 10
)
SELECT * FROM top_vendidos
UNION ALL
SELECT * FROM estoque_alto_venda_baixa
"""

r = supabase.rpc('conexo_executar_leitura', {'query_str': sql.strip()}).execute()
for row in r.data:
    print(row)
