import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

sql_ranking = """
CREATE OR REPLACE FUNCTION conexo_ranking_vendedores(
  p_tenant UUID, inicio DATE, fim DATE,
  p_rep TEXT DEFAULT NULL, limite INT DEFAULT 10
)
RETURNS JSON LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  SELECT JSON_AGG(r ORDER BY r.faturamento DESC)
  FROM (
    SELECT
      p.representante_codigo,
      MAX(p.representante_nome) AS vendedor,
      SUM(p.valor_total)        AS faturamento,
      SUM(p.quantidade_total)   AS metragem_vendida,
      COUNT(*)                AS total_pedidos
    FROM pedidos_totvs p
    INNER JOIN representantes rep ON rep.codigo = p.representante_codigo
    WHERE p.data_pedido::date BETWEEN inicio AND fim
      AND (p.status IS NULL OR LOWER(p.status) NOT LIKE '%canc%')
      AND rep.supervisor IS NOT NULL AND TRIM(rep.supervisor) <> ''
      AND rep.ativo IS TRUE
      AND (p_rep IS NULL OR p.representante_codigo = p_rep)
    GROUP BY p.representante_codigo
    ORDER BY faturamento DESC
    LIMIT limite
  ) r;
$$;
"""

try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": sql_ranking}).execute()
    print("Ranking RPC updated. Result:", res.data)
except Exception as e:
    print("Error updating Ranking RPC:", e)
