import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# 1. Inspect programacoes table
sql_prg = """
SELECT op, cod_tecido, nome_tecido, cod_cor, nome_cor, quantidade_solicitada, quantidade_disponivel
FROM programacoes
LIMIT 10
"""

res_prg = supabase.rpc("conexo_executar_leitura", {"query_str": sql_prg}).execute()
print("=== Sample programacoes ===")
for r in (res_prg.data or []):
    print(r)

# 2. Check matching reservations in pedidos_totvs & pedidos for colors/fabrics in programacoes
sql_reservas = """
WITH reservas AS (
    SELECT 
        TRIM(LOWER(item->>'colorCode')) as cod_cor,
        TRIM(LOWER(item->>'colorName')) as nome_cor,
        TRIM(LOWER(item->>'referenceName')) as nome_tecido,
        COALESCE(SUM((item->>'quantity')::numeric), 0) as metragem_reservada
    FROM pedidos_totvs p,
    LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(p.items_json) = 'array' THEN p.items_json ELSE '[]'::jsonb END) AS item
    WHERE p.status NOT IN ('Canceled', 'Attended')
    GROUP BY TRIM(LOWER(item->>'colorCode')), TRIM(LOWER(item->>'colorName')), TRIM(LOWER(item->>'referenceName'))
)
SELECT 
    pr.op,
    pr.nome_tecido,
    pr.nome_cor,
    pr.quantidade_solicitada,
    COALESCE(r.metragem_reservada, 0) as quantidade_reservada,
    GREATEST(0, pr.quantidade_solicitada - COALESCE(r.metragem_reservada, 0)) as quantidade_disponivel
FROM programacoes pr
LEFT JOIN reservas r ON (
    (pr.cod_cor IS NOT NULL AND LOWER(pr.cod_cor) = r.cod_cor)
    OR (LOWER(pr.nome_cor) = r.nome_cor)
    OR (LOWER(pr.nome_cor) LIKE '%' || r.nome_cor || '%')
)
ORDER BY quantidade_reservada DESC, pr.op DESC
LIMIT 15
"""

res_res = supabase.rpc("conexo_executar_leitura", {"query_str": sql_reservas}).execute()
print("\n=== Programacoes joined with Reservas ===")
for r in (res_res.data or []):
    print(r)
