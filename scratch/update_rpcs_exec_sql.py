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

sql_abaixo_meta = """
CREATE OR REPLACE FUNCTION conexo_vendedores_abaixo_meta(p_tenant UUID, inicio DATE, fim DATE)
RETURNS JSON LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  SELECT JSON_AGG(r ORDER BY r.percentual_atingido ASC)
  FROM (
    SELECT
      p.representante_codigo                                          AS vendedor,
      MAX(p.representante_nome)                                       AS vendedor_nome,
      SUM(p.quantidade_total)                                         AS metragem_vendida,
      SUM(p.valor_total)                                             AS faturado,
      MAX(rep.meta)                                                  AS meta_metros,
      ROUND(SUM(p.quantidade_total) / NULLIF(MAX(rep.meta),0) * 100, 1) AS percentual_atingido
    FROM pedidos_totvs p
    INNER JOIN representantes rep ON rep.codigo = p.representante_codigo
    WHERE p.data_pedido::date BETWEEN inicio AND fim
      AND (p.status IS NULL OR LOWER(p.status) NOT LIKE '%canc%')
      AND rep.supervisor IS NOT NULL AND TRIM(rep.supervisor) <> ''
      AND rep.ativo IS TRUE
    GROUP BY p.representante_codigo
    HAVING SUM(p.quantidade_total) < MAX(rep.meta)
  ) r;
$$;
"""

try:
    r1 = supabase.rpc("exec_sql", {"query": sql_ranking}).execute()
    print("Ranking RPC updated successfully:", r1.data)
except Exception as e:
    print("Error updating ranking RPC:", e)

try:
    r2 = supabase.rpc("exec_sql", {"query": sql_abaixo_meta}).execute()
    print("Abaixo Meta RPC updated successfully:", r2.data)
except Exception as e:
    print("Error updating abaixo meta RPC:", e)
