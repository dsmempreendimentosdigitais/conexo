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
        "description": "Relatório consolidado do período. Use para 'gere um relatório', 'resumo para reunião'.",
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
        "name": "conexo_consulta_geral",
        "description": (
            "Use esta ferramenta para responder perguntas personalizadas ou detalhadas que não "
            "se encaixam nas outras ferramentas pré-definidas. Exemplos: listar números de pedidos, "
            "detalhes de transações de ontem, ou agrupamentos específicos de vendas por cliente. "
            "Escreva uma consulta SQL PostgreSQL de leitura (SELECT) válida sobre as tabelas: "
            "- pedidos_totvs (id, totvs_order_code, totvs_order_id, data_pedido, data_faturamento, valor_total, valor_nf, quantidade_total, representante_codigo, representante_nome, cliente_nome, status, items_json) "
            "- representantes (codigo, nome, meta) "
            "ATENÇÃO IMPORTANTE PARA A CONSULTA SQL:\n"
            "1. Sempre use a coluna 'totvs_order_code' para se referir ao código/número legível do pedido (ex: 35828, 35806) em vez de 'id'.\n"
            "2. As colunas de data ('data_faturamento', 'data_pedido') são do tipo timestamp. Sempre use o cast '::date' ao comparar com strings de data (ex: 'data_pedido::date = ''2026-08-19''').\n"
            "3. REGRA CRÍTICA DE DATAS: Sempre que o usuário filtrar por qualquer data (ex: 'ontem', 'dia 19', 'no dia 19', 'esta semana', etc.), você DEVE usar a coluna 'data_pedido::date' para filtrar a data do pedido, pois o portal de vendas deles filtra exclusivamente pela data de criação. NUNCA use a coluna 'data_faturamento' para filtrar datas de forma geral (mesmo para perguntas contendo 'faturado' ou 'faturamento' como 'pedidos faturados no dia 19' ou 'faturamento de ontem'), caso contrário os números não baterão com o portal. Apenas use a coluna 'data_faturamento' se o usuário contiver explicitamente o termo 'data de faturamento real' ou 'data de faturamento do ERP'. Para perguntas de faturamento, filtre por data_pedido::date, use 'status IN (''Attended'', ''PartiallyAnswered'')' e some 'valor_nf'.\n"
            "4. Sempre ordene os resultados de forma recente e limite a consulta a no máximo 50 linhas."
        ),
        "parameters": {"type": "object", "properties": {
            "sql": {"type": "string", "description": "Consulta SQL PostgreSQL (SELECT) válida"}
        }, "required": ["sql"]}}},

    {"type": "function", "function": {
        "name": "fora_de_escopo",
        "description": "A pergunta não é sobre vendas, clientes, produtos, vendedores, metas ou mercado.",
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
