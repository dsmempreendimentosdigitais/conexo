TOOLS = [
    {"type": "function", "function": {
        "name": "conexo_vendas_periodo",
        "description": "Total faturado no período: faturamento, nº de pedidos e ticket médio. Use para 'como estão as vendas', 'quanto faturei', 'faturamento do mês'.",
        "parameters": {"type": "object", "properties": {
            "inicio": {"type": "string", "description": "Data inicial ISO AAAA-MM-DD"},
            "fim":    {"type": "string", "description": "Data final ISO AAAA-MM-DD"}
        }, "required": ["inicio", "fim"]}}},

    {"type": "function", "function": {
        "name": "conexo_comparativo_mes",
        "description": "Compara faturamento de um mês com o mês anterior. Use para 'comparar com mês passado', 'faturei mais que mês passado'.",
        "parameters": {"type": "object", "properties": {
            "mes_ref": {"type": "string", "description": "Mês de referência AAAA-MM"}
        }, "required": ["mes_ref"]}}},

    {"type": "function", "function": {
        "name": "conexo_comparativo_ano",
        "description": "Compara um período com o mesmo período do ano anterior. Use para 'comparar com ano passado', 'mesmo mês do ano passado'.",
        "parameters": {"type": "object", "properties": {
            "inicio": {"type": "string"}, "fim": {"type": "string"}
        }, "required": ["inicio", "fim"]}}},

    {"type": "function", "function": {
        "name": "conexo_ranking_vendedores",
        "description": "Ranking de representantes por faturamento. Use para 'melhores vendedores', 'ranking de vendas'.",
        "parameters": {"type": "object", "properties": {
            "inicio": {"type": "string"}, "fim": {"type": "string"},
            "limite": {"type": "integer", "description": "Quantos mostrar. Padrão 10."}
        }, "required": ["inicio", "fim"]}}},

    {"type": "function", "function": {
        "name": "conexo_vendedores_abaixo_meta",
        "description": "Representantes com faturamento abaixo da meta no período. Use para 'quem está abaixo da meta', 'quem não bateu meta'.",
        "parameters": {"type": "object", "properties": {
            "inicio": {"type": "string"}, "fim": {"type": "string"}
        }, "required": ["inicio", "fim"]}}},

    {"type": "function", "function": {
        "name": "conexo_top_produtos",
        "description": "Produtos mais faturados no período. Use para 'produtos mais vendidos', 'o que mais saiu'.",
        "parameters": {"type": "object", "properties": {
            "inicio": {"type": "string"}, "fim": {"type": "string"},
            "limite": {"type": "integer", "description": "Padrão 10."}
        }, "required": ["inicio", "fim"]}}},

    {"type": "function", "function": {
        "name": "conexo_top_clientes",
        "description": "Maiores clientes por faturamento no período. Use para 'melhores clientes', 'quem mais comprou'.",
        "parameters": {"type": "object", "properties": {
            "inicio": {"type": "string"}, "fim": {"type": "string"},
            "limite": {"type": "integer", "description": "Padrão 10."}
        }, "required": ["inicio", "fim"]}}},

    {"type": "function", "function": {
        "name": "conexo_clientes_inativos",
        "description": "Clientes que faturavam e pararam. Use para 'clientes inativos', 'quem parou de comprar'.",
        "parameters": {"type": "object", "properties": {
            "dias_sem_comprar": {"type": "integer", "description": "Dias sem faturar. Padrão 90."}
        }, "required": []}}},

    {"type": "function", "function": {
        "name": "conexo_vendas_regiao",
        "description": "Faturamento agrupado por UF/estado no período. Use para 'vendas por região', 'por estado'.",
        "parameters": {"type": "object", "properties": {
            "inicio": {"type": "string"}, "fim": {"type": "string"}
        }, "required": ["inicio", "fim"]}}},

    {"type": "function", "function": {
        "name": "conexo_top_cores",
        "description": "Cores mais vendidas no período. Use para 'quais cores vendi mais', 'cores mais vendidas', 'ranking de cores'.",
        "parameters": {"type": "object", "properties": {
            "inicio": {"type": "string"}, "fim": {"type": "string"},
            "limite": {"type": "integer", "description": "Padrão 10."}
        }, "required": ["inicio", "fim"]}}},

    {"type": "function", "function": {
        "name": "conexo_relatorio_periodo",
        "description": (
            "Relatório ou PDF consolidado do período com resumo de faturamento, top clientes, top produtos, ranking de vendedores e vendas por região. "
            "Use para: 'gere um relatório', 'resumo para reunião', 'gere um pdf', 'pdf do faturamento', 'exportar em pdf', "
            "'pdf de julho', 'relatório de agosto', 'me dê o pdf', 'quero um pdf', 'exportar dados', 'relatório completo'."
        ),
        "parameters": {"type": "object", "properties": {
            "inicio": {"type": "string"}, "fim": {"type": "string"}
        }, "required": ["inicio", "fim"]}}},

    # ---- Fase 2: Inteligência de Mercado ----
    {"type": "function", "function": {
        "name": "conexo_inteligencia_mercado",
        "description": (
            "Analisa o mercado, nicho, tendências, preços de insumos, concorrência "
            "ou notícias que afetam o negócio do cliente. "
            "Use para 'como está o mercado', 'tendências do meu setor', "
            "'preço do algodão', 'o mercado explica minha queda?'."
        ),
        "parameters": {"type": "object", "properties": {
            "assunto": {
                "type": "string",
                "description": "O tema de mercado a pesquisar."
            },
            "cruzar_com_interno": {
                "type": "boolean",
                "description": "Se true, também busca dado interno para cruzar."
            },
            "intent_interno": {
                "type": "string",
                "description": "RPC interna a buscar (ex.: conexo_top_produtos)."
            },
            "inicio": {"type": "string"},
            "fim":    {"type": "string"}
        }, "required": ["assunto"]}}},

    {"type": "function", "function": {
        "name": "conexo_consulta_estoque",
        "description": "Consulta disponibilidade de tecidos e cores no estoque de pronto-entrega (tabela estoque_pe). Use para 'tem cor bege no estoque?', 'tem tricoline paris?', 'quanto temos de bege areia no estoque?', 'disponibilidade de produto'.",
        "parameters": {"type": "object", "properties": {
            "produto": {"type": "string", "description": "Nome ou tipo do tecido (ex: tricoline paris, tricoline havana, sarja)"},
            "cor":     {"type": "string", "description": "Nome ou código da cor (ex: bege areia, 240, marinho)"}
        }, "required": []}}},

    {"type": "function", "function": {
        "name": "conexo_consulta_programacao",
        "description": "Consulta tecidos, cores, previsões de faturamento e metragens na programação de produção do PCP (tabela programacoes). Use para 'o que tem na programação?', 'quanto metros de off white na programação?', 'previsão da linha ilhabela rustic', 'tecido X na produção'.",
        "parameters": {"type": "object", "properties": {
            "produto": {"type": "string", "description": "Nome ou código do tecido (ex: ilhabela rustic, sarja prowork)"},
            "cor":     {"type": "string", "description": "Nome ou código da cor (ex: off white, 001, 100, azul maya)"}
        }, "required": []}}},

    {"type": "function", "function": {
        "name": "conexo_consulta_pedidos",
        "description": (
            "Consulta e gera relatório/PDF de pedidos unificando o Portal de Vendas (pedidos + pedido_itens, incluindo pedidos locais W... bloqueados) "
            "com o ERP TOTVS (pedidos_totvs), com 100% de precisão na metragem e valor total por pedido. "
            "Use SEMPRE para: 'liste todos os pedidos em andamento e bloqueados do artigo X', 'gere um pdf com os pedidos do artigo 1117 - sarja dakota', "
            "'quais os pedidos bloqueados?', 'pedidos em andamento de tal tecido/cor/cliente/representante', 'relatório resumido de pedidos'."
        ),
        "parameters": {"type": "object", "properties": {
            "artigo":        {"type": "string", "description": "Código ou nome do artigo/tecido (ex: '1117 - sarja dakota', '1117', 'sarja dakota', 'linho deluxe'). Vazio para todos."},
            "cor":           {"type": "string", "description": "Código ou nome da cor/desenho (ex: '900', 'preto', 'off white'). Vazio para todas."},
            "status_filtro": {"type": "string", "description": "Filtro de status: 'carteira' (Em andamento + Bloqueado + Em composição + Em análise, padrão para pedidos em andamento e bloqueados), 'bloqueados' (apenas Bloqueado), 'em_andamento' (apenas Em andamento), 'faturados' (Atendido + Parcialmente Atendido), ou 'todos'."},
            "cliente":       {"type": "string", "description": "Nome ou razão social do cliente (opcional)."},
            "representante": {"type": "string", "description": "Código ou nome do representante (opcional)."},
            "inicio":        {"type": "string", "description": "Data inicial ISO AAAA-MM-DD (padrão '2026-01-01')."},
            "fim":           {"type": "string", "description": "Data final ISO AAAA-MM-DD (padrão data atual)."}
        }, "required": []}}},

    {"type": "function", "function": {
        "name": "conexo_consulta_geral",
        "description": (
            "Use esta ferramenta para responder perguntas personalizadas ou detalhadas que não "
            "se encaixam nas outras ferramentas pré-definidas. Exemplos: "
            "detalhes de transações de ontem, agrupamentos específicos de vendas por cliente, ou cruzamento de estoque com vendas. "
            "Escreva uma consulta SQL PostgreSQL de leitura (SELECT) válida sobre as tabelas: "
            "- pedidos_totvs (id, totvs_order_code, totvs_order_id, data_pedido, data_faturamento, valor_total, valor_nf, quantidade_total, representante_codigo, representante_nome, cliente_nome, status, items_json) "
            "- clientes (id, codigo, razao_social, nome_fantasia, representante_codigo, cidade, uf, limite_credito, saldo_disponivel, telefone, email, status_cliente) "
            "- pedidos (tabela do PORTAL DE VENDAS vendas.designtex.com.br — contém id, numero, status, valor_total, created_at, cliente_id, representante_codigo. Para pedidos BLOQUEADOS ou no FORÇA DE VENDAS, use esta tabela fazendo JOIN clientes c ON c.id = p.cliente_id e JOIN representantes r ON r.codigo = p.representante_codigo!) "
            "- representantes (codigo, nome, meta, supervisor, ativo, cidade) "
            "- estoque_pe (cod_produto, descricao, cor, cor_codigo, quantidade_disponivel, categoria, unidade) "
            "- programacoes (op, cod_tecido, nome_tecido, cod_cor, nome_cor, quantidade_solicitada, quantidade_disponivel, previsao_faturamento, tipo) "
            "ATENÇÃO IMPORTANTE PARA A CONSULTA SQL:\n"
            "1. Sempre use a coluna 'totvs_order_code' para se referir ao código/número legível do pedido (ex: 35828, 35806) em vez de 'id'.\n"
            "2. As colunas de data ('data_faturamento', 'data_pedido') são do tipo timestamp. Sempre use o cast '::date' ao comparar com strings de data (ex: 'data_pedido::date = ''2026-08-19''').\n"
            "3. REGRA CRÍTICA DE DATAS E PEDIDOS BLOQUEADOS:\n"
            "   a) Faturamento/Vendas concluídas: Use `pedidos_totvs`, `nota_fiscal_data::date`, `valor_nf` e `status IN ('Attended', 'PartiallyAnswered')`.\n"
            "   b) Pedidos BLOQUEADOS / Aprovação no Força de Vendas (vendas.designtex.com.br): DEVE consultar a tabela `pedidos` (Portal de Vendas) com JOIN clientes c ON c.id = p.cliente_id e JOIN representantes r ON r.codigo = p.representante_codigo, filtrando `WHERE p.status = 'Bloqueado' AND p.valor_total > 0`.\n"
            "4. REGRA OBRIGATÓRIA CONTRA PEDIDOS ZERADOS: NUNCA inclua pedidos com `valor_total = 0` ou `valor_total IS NULL`. Sempre adicione a condição `valor_total > 0` (ou `p.valor_total > 0`).\n"
            "5. CONSULTAS EM ITEMS_JSON: Para buscar por produto, estampa ou cor dentro dos pedidos_totvs:\n"
            "   a) Busca simples por produto/estampa no JSON: Use `p.items_json::text ILIKE '%estamp%'` (ex: para desenhos, estampados, produtos).\n"
            "   b) Expansão de itens com LATERAL: Use SEMPRE a sintaxe `CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(p.items_json) = 'array' THEN p.items_json ELSE '[]'::jsonb END) AS item`. NUNCA use 'LATERAL' sozinho sem CROSS JOIN e NUNCA use 'LATERAL JOIN' (isso causa erro 42601 no PostgreSQL).\n"
            "   c) ATENÇÃO CRÍTICA AO VALOR DO ITEM NO JSON: O campo `item->>'totalValue'` NÃO EXISTE no JSON! NUNCA use `item->>'totalValue'`. Para calcular o valor em R$ de um item do `items_json`, use SEMPRE: `(COALESCE((item->>'settledQuantity')::numeric, (item->>'quantity')::numeric, 0) * COALESCE((item->>'price')::numeric, 0))`.\n"
            "   d) ATENÇÃO CRÍTICA AO CRUZAR `estoque_pe` COM `items_json`: Na tabela `estoque_pe`, `cod_produto` contém apenas números (ex: '1033', '1044'), enquanto no `items_json`, `item->>'referenceCode'` possui prefixos de texto (ex: 'PA LISO 1033', 'PA EST 1044'). Para fazer JOIN entre `estoque_pe` e `items_json`, extraia os dígitos com `regexp_replace(COALESCE(item->>'referenceCode', ''), '[^0-9]', '', 'g') = ep.cod_produto AND TRIM(COALESCE(item->>'colorCode', '')) = ep.cor_codigo`!\n"
            "   Exemplo: SELECT p.totvs_order_code, p.cliente_nome, p.data_pedido::date, item->>'referenceName' as produto, item->>'colorName' as cor, (item->>'quantity')::numeric as metragem, ROUND((COALESCE((item->>'quantity')::numeric, 0) * COALESCE((item->>'price')::numeric, 0)), 2) as valor FROM pedidos_totvs p CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(p.items_json) = 'array' THEN p.items_json ELSE '[]'::jsonb END) AS item WHERE item->>'colorName' ILIKE '%Caqui Tangelo%' ORDER BY p.data_pedido DESC LIMIT 20;\n"
            "6. NUNCA coloque funções de retorno de conjunto como jsonb_array_elements(...) dentro de funções agregadoras como SUM() ou COUNT(). Em vez disso, use `CROSS JOIN LATERAL jsonb_array_elements(...) AS item` no FROM.\n"
            "7. REGRA CRÍTICA PARA CONSULTAS DE PEDIDOS E CARTEIRA: Sempre que o usuário perguntar por pedidos em andamento, carteira ou listagem de pedidos de vendas, você DEVE incluir na consulta SQL as colunas de totalização global usando Window Functions simples SEM DISTINCT:\n"
            "   `COUNT(*) OVER() AS total_pedidos_geral, SUM(valor_total) OVER() AS valor_total_geral, SUM(quantidade_total) OVER() AS metragem_total_geral`.\n"
            "   ATENÇÃO: NUNCA use `COUNT(DISTINCT ...) OVER()` pois o PostgreSQL não suporta DISTINCT em Window Functions (erro 0A000!). Use apenas `COUNT(*) OVER()`.\n"
            "8. REGRA CRÍTICA PARA REPRESENTANTES E VENDEDORES: Sempre que a consulta envolver representantes/vendedores, você DEVE obrigatoriamente fazer `INNER JOIN representantes rep ON rep.codigo = p.representante_codigo` e filtrar `rep.supervisor IS NOT NULL AND TRIM(rep.supervisor) <> '' AND rep.ativo IS TRUE`. NUNCA traga representantes inativos, sem supervisor ou códigos de apoio TOTVS ('REPRESENTANTE TOTVS #...').\n"
            "9. CONSULTAS PCP E PROGRAMAÇÃO DE PRODUÇÃO (programacoes): Sempre que consultar a tabela `programacoes`, selecione obrigatoriamente `op, cod_tecido, nome_tecido, cod_cor, nome_cor, quantidade_solicitada, quantidade_disponivel, GREATEST(0, quantidade_solicitada - quantidade_disponivel) AS quantidade_reservada, previsao_faturamento, tipo` para que a metragem reservada/vendida seja exibida corretamente no gráfico em pizza e na tabela.\n"
            "10. ANÁLISES ESTRATÉGICAS, POTENCIAL DE CRESCIMENTO E PLANOS DE AÇÃO: Use SEMPRE esta ferramenta para perguntas estratégicas sobre representantes e vendedores (ex: 'potencial de crescimento do André', 'expectativa de vendas', 'nicho dos clientes e tamanho de carteira', 'plano de ação para a Designtex apoiar o representante'). Monte uma query rica agrupando por cliente e somando o faturamento total do representante no pedidos_totvs.\n"
            "11. ATENÇÃO ABSOLUTA À COLUNA 'uf' E 'cidade': As colunas 'uf' e 'cidade' pertencem à tabela 'clientes'. As tabelas 'representantes' e 'pedidos_totvs' NÃO POSSUEM coluna 'uf' (a tabela 'representantes' tem apenas 'cidade' em formato 'CIDADE / UF', e 'pedidos_totvs' não possui nem 'uf' nem 'cidade'). NUNCA use 'p.uf' nem 'r.uf'. Para consultas por estado/UF ou cidades de clientes e prospecção de carteira, consulte a tabela 'clientes c' ou faça JOIN com 'clientes c'!"
        ),
        "parameters": {"type": "object", "properties": {
            "sql": {"type": "string", "description": "Consulta SQL PostgreSQL (SELECT) válida"}
        }, "required": ["sql"]}}},

    {"type": "function", "function": {
        "name": "fora_de_escopo",
        "description": "A pergunta NÃO tem qualquer relação com o negócio da empresa (ex: futebol, previsão do tempo pessoal, receitas culinárias). NUNCA use fora_de_escopo para perguntas estratégicas, de vendas, clientes, representantes/vendedores, planos de ação comercial, produtos ou metas!",
        "parameters": {"type": "object", "properties": {
            "motivo": {"type": "string"}
        }, "required": ["motivo"]}}},

    {"type": "function", "function": {
        "name": "pedir_esclarecimento",
        "description": "Falta informação essencial e não dá pra inferir.",
        "parameters": {"type": "object", "properties": {
            "pergunta_ao_usuario": {"type": "string"}
        }, "required": ["pergunta_ao_usuario"]}}},
]
