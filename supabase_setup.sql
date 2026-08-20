-- ============================================================
-- CONEXO v2.0 — SQL completo de setup no Supabase
-- Execute no SQL Editor do seu projeto Supabase
-- ORDEM IMPORTA: meu_tenant() é criada antes das policies
-- ============================================================

-- -------------------------------------------------------
-- 1. TENANTS — empresas clientes
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cnpj            TEXT UNIQUE NOT NULL,
  nome            TEXT NOT NULL,
  ativo           BOOLEAN DEFAULT TRUE,
  perfil_mercado  JSONB,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------
-- 2. USUÁRIOS vinculados a um tenant
-- (sem RLS aqui — backend usa service_role que bypassa RLS)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS conexo_usuarios (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_user_id         UUID UNIQUE,
  tenant_id            UUID NOT NULL REFERENCES tenants(id),
  email                TEXT UNIQUE NOT NULL,
  setor                TEXT,
  perfil               TEXT NOT NULL DEFAULT 'gestor',
  representante_codigo TEXT,
  ativo                BOOLEAN DEFAULT TRUE,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conexo_usuarios_auth   ON conexo_usuarios(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_conexo_usuarios_tenant ON conexo_usuarios(tenant_id);

-- -------------------------------------------------------
-- 3. FUNÇÃO meu_tenant() — criada ANTES das policies RLS
--    Lê o tenant do usuário logado via Supabase Auth
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION meu_tenant()
RETURNS UUID LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  SELECT tenant_id FROM conexo_usuarios
  WHERE auth_user_id = auth.uid();
$$;

-- -------------------------------------------------------
-- 4. AUDITORIA de consultas
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS conexo_logs (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  usuario     TEXT,
  pergunta    TEXT,
  intent      TEXT,
  parametros  JSONB,
  sucesso     BOOLEAN,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conexo_logs_usuario    ON conexo_logs(usuario);
CREATE INDEX IF NOT EXISTS idx_conexo_logs_created_at ON conexo_logs(created_at DESC);

-- -------------------------------------------------------
-- 5. ALERTAS proativos (internos + mercado)
--    RLS usa meu_tenant() — precisa estar criada antes (passo 3)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS conexo_alertas (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id   UUID REFERENCES tenants(id),
  tipo        TEXT,
  severidade  TEXT,
  mensagem    TEXT,
  dados       JSONB,
  lido        BOOLEAN DEFAULT FALSE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE conexo_alertas ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON conexo_alertas;
CREATE POLICY tenant_isolation ON conexo_alertas
  FOR SELECT USING (tenant_id = meu_tenant());

-- -------------------------------------------------------
-- 6. ONBOARDING técnico por IA
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS conexo_onboarding (
  cnpj         TEXT PRIMARY KEY,
  mapeamento   JSONB,
  rpcs_geradas JSONB,
  status       TEXT DEFAULT 'aguardando_revisao',
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------
-- 7. RPCs das 11 ferramentas do CONEXO (Mapeadas para TOTVS Moda)
-- -------------------------------------------------------

-- 7.1 Vendas por período
CREATE OR REPLACE FUNCTION conexo_vendas_periodo(
  p_tenant UUID, inicio DATE, fim DATE,
  p_rep TEXT DEFAULT NULL
)
RETURNS JSON LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  SELECT JSON_BUILD_OBJECT(
    'carteira_valor',      COALESCE(SUM(valor_total) FILTER (WHERE data_pedido::date BETWEEN inicio AND fim AND (status IS NULL OR LOWER(status) NOT LIKE '%canc%')), 0),
    'carteira_metragem',   COALESCE(SUM(quantidade_total) FILTER (WHERE data_pedido::date BETWEEN inicio AND fim AND (status IS NULL OR LOWER(status) NOT LIKE '%canc%')), 0),
    'faturado_valor',      COALESCE(SUM(valor_total) FILTER (WHERE data_faturamento::date BETWEEN inicio AND fim), 0),
    'faturado_metragem',   COALESCE(SUM(quantidade_total) FILTER (WHERE data_faturamento::date BETWEEN inicio AND fim), 0),
    'total_pedidos',       COUNT(id) FILTER (WHERE data_pedido::date BETWEEN inicio AND fim AND (status IS NULL OR LOWER(status) NOT LIKE '%canc%'))
  )
  FROM pedidos_totvs
  WHERE (p_rep IS NULL OR representante_codigo = p_rep);
$$;

-- 7.2 Comparativo mês vs mês anterior
CREATE OR REPLACE FUNCTION conexo_comparativo_mes(p_tenant UUID, mes_ref TEXT)
RETURNS JSON LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  WITH
    ref AS (
      SELECT 
        COALESCE(SUM(valor_total),0) AS fat_val,
        COALESCE(SUM(quantidade_total),0) AS fat_met
      FROM pedidos_totvs
      WHERE TO_CHAR(data_faturamento, 'YYYY-MM') = mes_ref
    ),
    ant AS (
      SELECT 
        COALESCE(SUM(valor_total),0) AS fat_val,
        COALESCE(SUM(quantidade_total),0) AS fat_met
      FROM pedidos_totvs
      WHERE TO_CHAR(data_faturamento, 'YYYY-MM') =
            TO_CHAR((TO_DATE(mes_ref||'-01','YYYY-MM-DD') - INTERVAL '1 month'),'YYYY-MM')
    )
  SELECT JSON_BUILD_OBJECT(
    'mes_ref', mes_ref,
    'valor_ref', ref.fat_val,
    'metragem_ref', ref.fat_met,
    'valor_ant', ant.fat_val,
    'metragem_ant', ant.fat_met
  ) FROM ref, ant;
$$;

-- 7.3 Comparativo período vs mesmo período ano anterior
CREATE OR REPLACE FUNCTION conexo_comparativo_ano(p_tenant UUID, inicio DATE, fim DATE)
RETURNS JSON LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  WITH
    atual AS (
      SELECT 
        COALESCE(SUM(valor_total),0) AS fat_val,
        COALESCE(SUM(quantidade_total),0) AS fat_met
      FROM pedidos_totvs
      WHERE data_faturamento::date BETWEEN inicio AND fim
    ),
    anterior AS (
      SELECT 
        COALESCE(SUM(valor_total),0) AS fat_val,
        COALESCE(SUM(quantidade_total),0) AS fat_met
      FROM pedidos_totvs
      WHERE data_faturamento::date BETWEEN
            (inicio - INTERVAL '1 year') AND (fim - INTERVAL '1 year')
    )
  SELECT JSON_BUILD_OBJECT(
    'valor_atual', atual.fat_val,
    'metragem_atual', atual.fat_met,
    'valor_anterior', anterior.fat_val,
    'metragem_anterior', anterior.fat_met
  ) FROM atual, anterior;
$$;

-- 7.4 Ranking de vendedores
CREATE OR REPLACE FUNCTION conexo_ranking_vendedores(
  p_tenant UUID, inicio DATE, fim DATE,
  p_rep TEXT DEFAULT NULL, limite INT DEFAULT 10
)
RETURNS JSON LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  SELECT JSON_AGG(r ORDER BY r.metragem_vendida DESC)
  FROM (
    SELECT
      representante_codigo,
      MAX(representante_nome) AS vendedor,
      SUM(valor_total)        AS faturamento,
      SUM(quantidade_total)   AS metragem_vendida,
      COUNT(*)                AS total_pedidos
    FROM pedidos_totvs
    WHERE data_pedido::date BETWEEN inicio AND fim
      AND (status IS NULL OR LOWER(status) NOT LIKE '%canc%')
      AND (p_rep IS NULL OR representante_codigo = p_rep)
    GROUP BY representante_codigo
    LIMIT limite
  ) r;
$$;

-- 7.5 Vendedores abaixo da meta (Expectativa)
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
    LEFT JOIN representantes rep ON rep.codigo = p.representante_codigo
    WHERE p.data_pedido::date BETWEEN inicio AND fim
      AND (p.status IS NULL OR LOWER(p.status) NOT LIKE '%canc%')
    GROUP BY p.representante_codigo
    HAVING SUM(p.quantidade_total) < MAX(rep.meta)
  ) r;
$$;

-- 7.6 Top produtos (Metragem e Valor)
CREATE OR REPLACE FUNCTION conexo_top_produtos(
  p_tenant UUID, inicio DATE, fim DATE,
  p_rep TEXT DEFAULT NULL, limite INT DEFAULT 10
)
RETURNS JSON LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  SELECT JSON_AGG(r ORDER BY r.metragem DESC)
  FROM (
    SELECT
      item."referenceName" AS produto,
      SUM(item.quantity)   AS metragem,
      SUM(item.quantity * item.price) AS faturamento
    FROM pedidos_totvs p,
    LATERAL jsonb_to_recordset(p.items_json) AS item(
      "referenceName" text, 
      quantity numeric, 
      price numeric
    )
    WHERE p.data_pedido::date BETWEEN inicio AND fim
      AND (p.status IS NULL OR LOWER(p.status) NOT LIKE '%canc%')
      AND (p_rep IS NULL OR p.representante_codigo = p_rep)
    GROUP BY item."referenceName"
    ORDER BY metragem DESC
    LIMIT limite
  ) r;
$$;

-- 7.7 Top clientes (Metragem e Valor)
CREATE OR REPLACE FUNCTION conexo_top_clientes(
  p_tenant UUID, inicio DATE, fim DATE,
  p_rep TEXT DEFAULT NULL, limite INT DEFAULT 10
)
RETURNS JSON LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  SELECT JSON_AGG(r ORDER BY r.faturamento DESC)
  FROM (
    SELECT
      cliente_nome     AS cliente,
      COUNT(*)         AS total_pedidos,
      SUM(valor_total) AS faturamento,
      SUM(quantidade_total) AS metragem_vendida
    FROM pedidos_totvs
    WHERE data_pedido::date BETWEEN inicio AND fim
      AND (status IS NULL OR LOWER(status) NOT LIKE '%canc%')
      AND (p_rep IS NULL OR representante_codigo = p_rep)
    GROUP BY cliente_nome
    ORDER BY faturamento DESC
    LIMIT limite
  ) r;
$$;

-- 7.8 Clientes inativos
CREATE OR REPLACE FUNCTION conexo_clientes_inativos(
  p_tenant UUID, dias_sem_comprar INT DEFAULT 90
)
RETURNS JSON LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  SELECT JSON_AGG(r ORDER BY r.ultima_compra ASC)
  FROM (
    SELECT
      cliente_nome                              AS cliente,
      MAX(data_faturamento)::date               AS ultima_compra,
      SUM(valor_total)                          AS faturamento_historico,
      COUNT(*)                                  AS total_pedidos,
      (NOW()::date - MAX(data_faturamento)::date) AS dias_inativo
    FROM pedidos_totvs
    WHERE data_faturamento IS NOT NULL
    GROUP BY cliente_nome
    HAVING MAX(data_faturamento)::date < (NOW() - (dias_sem_comprar||' days')::INTERVAL)::date
  ) r;
$$;

-- 7.9 Vendas por região (UF)
CREATE OR REPLACE FUNCTION conexo_vendas_regiao(
  p_tenant UUID, inicio DATE, fim DATE,
  p_rep TEXT DEFAULT NULL
)
RETURNS JSON LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  SELECT JSON_AGG(r ORDER BY r.faturamento DESC)
  FROM (
    SELECT
      c.uf             AS uf,
      COUNT(*)         AS total_pedidos,
      SUM(p.valor_total) AS faturamento,
      SUM(p.quantidade_total) AS metragem_vendida
    FROM pedidos_totvs p
    LEFT JOIN clientes c ON c.codigo = p.cliente_codigo
    WHERE p.data_pedido::date BETWEEN inicio AND fim
      AND (p.status IS NULL OR LOWER(p.status) NOT LIKE '%canc%')
      AND (p_rep IS NULL OR p.representante_codigo = p_rep)
    GROUP BY c.uf
  ) r;
$$;

-- 7.10 Cores mais vendidas (Extraída dos Itens do Pedido)
CREATE OR REPLACE FUNCTION conexo_top_cores(
  p_tenant UUID, inicio DATE, fim DATE,
  p_rep TEXT DEFAULT NULL, limite INT DEFAULT 10
)
RETURNS JSON LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  SELECT JSON_AGG(r ORDER BY r.metragem DESC)
  FROM (
    SELECT
      item."colorName"    AS cor,
      SUM(item.quantity)  AS metragem,
      SUM(item.quantity * item.price) AS faturamento
    FROM pedidos_totvs p,
    LATERAL jsonb_to_recordset(p.items_json) AS item(
      "colorName" text, 
      quantity numeric, 
      price numeric
    )
    WHERE p.data_pedido::date BETWEEN inicio AND fim
      AND (p.status IS NULL OR LOWER(p.status) NOT LIKE '%canc%')
      AND (p_rep IS NULL OR p.representante_codigo = p_rep)
    GROUP BY item."colorName"
    ORDER BY metragem DESC
    LIMIT limite
  ) r;
$$;

-- 7.11 Relatório consolidado
CREATE OR REPLACE FUNCTION conexo_relatorio_periodo(p_tenant UUID, inicio DATE, fim DATE)
RETURNS JSON LANGUAGE SQL STABLE SECURITY DEFINER AS $$
  SELECT JSON_BUILD_OBJECT(
    'resumo',             conexo_vendas_periodo(p_tenant, inicio, fim),
    'top_clientes',       conexo_top_clientes(p_tenant, inicio, fim, NULL, 5),
    'top_produtos',       conexo_top_produtos(p_tenant, inicio, fim, NULL, 5),
    'ranking_vendedores', conexo_ranking_vendedores(p_tenant, inicio, fim, NULL, 5),
    'por_regiao',         conexo_vendas_regiao(p_tenant, inicio, fim)
  );
$$;

-- -------------------------------------------------------
-- 8. RPC de ALERTAS INTERNOS (job diário)
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION conexo_detectar_alertas(p_tenant UUID)
RETURNS TABLE(tipo TEXT, severidade TEXT, mensagem TEXT, dados JSONB)
LANGUAGE PLPGSQL STABLE SECURITY DEFINER AS $$
DECLARE
  fat_atual    NUMERIC;
  fat_anterior NUMERIC;
BEGIN
  SELECT COALESCE(SUM(valor_total),0) INTO fat_atual FROM pedidos_totvs
   WHERE data_faturamento::DATE >= CURRENT_DATE - 7;

  SELECT COALESCE(SUM(valor_total),0) INTO fat_anterior FROM pedidos_totvs
   WHERE data_faturamento::DATE BETWEEN CURRENT_DATE - 14 AND CURRENT_DATE - 8;

  IF fat_anterior > 0 AND fat_atual < fat_anterior * 0.85 THEN
    tipo       := 'queda_faturamento';
    severidade := 'alta';
    mensagem   := FORMAT('Faturamento caiu %s%% nesta semana vs a anterior.',
                         ROUND((1 - fat_atual / fat_anterior) * 100));
    dados      := JSONB_BUILD_OBJECT('atual', fat_atual, 'anterior', fat_anterior);
    RETURN NEXT;
  END IF;

  RETURN QUERY
    SELECT
      'cliente_inativo'::TEXT,
      'media'::TEXT,
      FORMAT('%s: sem comprar há mais de 60 dias.', cliente_nome),
      JSONB_BUILD_OBJECT('cliente', cliente_nome)
    FROM pedidos_totvs
    WHERE data_faturamento IS NOT NULL
    GROUP BY cliente_nome
    HAVING MAX(data_faturamento)::DATE BETWEEN CURRENT_DATE - 180 AND CURRENT_DATE - 60
       AND MAX(data_faturamento)::DATE < CURRENT_DATE - 60
    LIMIT 5;
END;
$$;

) ON CONFLICT (cnpj) DO UPDATE SET nome = EXCLUDED.nome, perfil_mercado = EXCLUDED.perfil_mercado;


-- -------------------------------------------------------
-- 10. Função para execução de consultas de leitura dinâmicas (Text-to-SQL)
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION conexo_executar_leitura(query_str text)
RETURNS json LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  ret json;
BEGIN
  -- Bloqueio estrito de qualquer alteração de escrita por segurança
  IF LOWER(query_str) LIKE '%insert%' OR 
     LOWER(query_str) LIKE '%update%' OR 
     LOWER(query_str) LIKE '%delete%' OR 
     LOWER(query_str) LIKE '%drop%' OR 
     LOWER(query_str) LIKE '%alter%' OR 
     LOWER(query_str) LIKE '%truncate%' OR
     LOWER(query_str) LIKE '%create%' OR
     LOWER(query_str) LIKE '%grant%' THEN
    RAISE EXCEPTION 'Apenas consultas de leitura (SELECT) são permitidas.';
  END IF;
  
  EXECUTE 'SELECT json_agg(t) FROM (' || query_str || ') t' INTO ret;
  RETURN COALESCE(ret, '[]'::json);
END;
$$;


