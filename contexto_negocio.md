# CONTEXTO DE NEGÓCIO — DESIGNTEX TECIDOS
# Documento de inteligência interna do CONEXO
# Gerado automaticamente por varredura do Supabase em 2026-08-26

## EMPRESA
- **Nome:** Designtex Indústria e Comércio de Tecidos Ltda
- **Segmento:** Indústria têxtil — fabricação e venda de tecidos planos (tricoline, sarja, etc.)
- **Canal de vendas:** Via representantes comerciais em todo o Brasil
- **Portal:** vendas.designtex.com.br (Força de Vendas)
- **ERP:** TOTVS (sincronizado via API com o Supabase)

## STATUS DE PEDIDOS (TOTVS)

| Status (banco) | Tradução | Sinônimos em PT-BR | Qtd atual | Valor total |
|---|---|---|---|---|
| Attended | Atendido/Faturado | faturado, entregue, concluído | 7.816 | R$ 104,3 mi |
| Canceled | Cancelado | cancelado, desistência | 787 | R$ 26,5 mi |
| InProgress | Em andamento/Carteira | em aberto, carteira, pendente, não faturado | 334 | R$ 7,2 mi |
| PartiallyAnswered | Parcialmente faturado | parcial, entregue parcialmente | 99 | R$ 2,9 mi |
| Blocked | Bloqueado | bloqueado, retido, em bloqueio, travado | 19 | R$ 11,1 mil |
| InComposition | Em composição | em composição, sendo montado | 3 | R$ 0 |

## TABELA DE PROGRAMAÇÃO PCP (programacoes)

Uso: Consultas de tecidos em produção na fábrica, metragens programadas, OPs e previsão de faturamento.
Campos principais:
- `op`: Número da Ordem de Produção (ex: "2026.268 - LISO")
- `cod_tecido`: Código do tecido (ex: "1118")
- `nome_tecido`: Nome da linha do tecido (ex: "ILHABELA RUSTIC", "SARJA PROWORK")
- `cod_cor`: Código da cor (ex: "001", "100", "760")
- `nome_cor`: Nome da cor (ex: "Off White", "Branco", "Azul Maya")
- `quantidade_solicitada`: Metragem total programada na fábrica
- `quantidade_disponivel`: Metragem ainda disponível para venda
- `previsao_faturamento`: Previsão de saída da produção (ex: "3ª semana de outubro")
- `tipo`: Categoria ("liso", "estampado", "esgotado")

## REGRAS CRÍTICAS DE DADOS

FATURAMENTO: usar nota_fiscal_data::date como filtro de data, valor_nf como valor, status IN ('Attended','PartiallyAnswered')
CARTEIRA EM ANDAMENTO: usar data_pedido::date, valor_total, status IN ('InProgress','Blocked','InComposition')
PEDIDOS BLOQUEADOS / PORTAL DE VENDAS (vendas.designtex.com.br): Usar a tabela `pedidos` (Portal de Vendas), JOIN clientes c ON c.id = p.cliente_id, JOIN representantes r ON r.codigo = p.representante_codigo, onde `p.status = 'Bloqueado'` e `p.valor_total > 0`.
FILTRO DE VALOR ZERADO (OBRIGATÓRIO): NUNCA inclua pedidos com `valor_total = 0` ou `valor_total IS NULL` em listagens de pedidos, carteira ou bloqueados. Adicione SEMPRE `valor_total > 0`.
CÓDIGO DO PEDIDO: sempre usar totvs_order_code ou numero (ex: 35828 ou W001347GIGI), nunca id interno
META PADRÃO: R$ 10.000/mês por representante
TIMEZONE: UTC no banco, exibir em Brasília (UTC-3)

## CAMPOS DA TABELA pedidos (Portal de Vendas — vendas.designtex.com.br)

- `numero`: código legível do pedido no portal (ex: "W001347GIGI", "36554")
- `status`: status no portal (ex: "Bloqueado", "Atendido", "Aprovado", "Cancelado")
- `valor_total`: valor total do pedido no portal
- `created_at`: data de criação do pedido no portal (usar `created_at::date`)
- `cliente_id`: ID para JOIN com `clientes c ON c.id = p.cliente_id` (`c.razao_social AS cliente_nome`)
- `representante_codigo`: código para JOIN com `representantes r ON r.codigo = p.representante_codigo` (`r.nome AS representante_nome`)

## CAMPOS DA TABELA pedidos_totvs

totvs_order_code - número legível do pedido (ex: 35828)
totvs_order_id - ID interno TOTVS (não exibir ao usuário)
cliente_nome - razão social do cliente
representante_nome - nome do representante
status - status do pedido (ver tabela acima)
status_forca_vendas - status interno do portal
data_pedido - data de criação do pedido
nota_fiscal_data - DATA DE EMISSÃO DA NF-e (usar para faturamento)
nota_fiscal_numero - número da nota fiscal
valor_total - valor do pedido (carteira)
valor_nf - VALOR FATURADO na NF-e (usar para faturamento)
valor_frete - valor do frete
valor_desconto - desconto concedido
quantidade_total - quantidade em metros/unidades
condicao_pagamento - condição de pagamento
tabela_preco - tabela de preços aplicada
transportadora - nome da transportadora
tipo_frete - CIF ou FOB
previsao_faturamento - data prevista de faturamento
pedido_compra - número do pedido de compra do cliente
triangular - se é venda triangular (boolean)
items_json - array de itens do pedido (jsonb)
invoices_json - array de notas fiscais (jsonb)

## ESTRUTURA DO items_json (cada item)

name - nome completo do produto+cor (ex: "TRICOLINE PARIS 302 ROSA PINK REF# 200/55 U")
price - preço unitário atual
originalPrice - preço original (antes de desconto)
quantity - quantidade pedida
settledQuantity - quantidade faturada
pendingQuantity - quantidade pendente
canceledQuantity - quantidade cancelada
colorCode - código da cor (ex: "302")
colorName - nome da cor (ex: "302 ROSA PINK REF# 200/55")
referenceName - nome da linha (ex: "TRICOLINE PARIS PLUS 100% ALGODAO")
referenceCode - código da referência (ex: "PA LISO 1010")
productCode - código interno do produto
sizeName - tamanho (normalmente "U" = único)

## CAMPOS DA TABELA representantes

codigo - código no TOTVS (chave de ligação com pedidos_totvs.representante_codigo)
nome - nome completo
email / email_login - e-mail de acesso
meta - meta mensal em R$ (padrão: 10000)
ativo - se está ativo (boolean)
supervisor - nome do supervisor
cidade - cidade base

## REPRESENTANTES ATIVOS (lista completa)

GENESIS COMERCIO DE TECIDOS E ALIMENTICIOS E REPRESENTACOES
RAJ ALLIANCE REPRESENTACAO COMERCIAL DE TECIDOS LTDA
ALUKI PROMOCAO DE VENDAS LTDA
A FERNANDES REP COM DE TECIDOS E CONFECCOES (conhecido comercialmente como André / André Fernandes — código TOTVS: 3019 — supervisora: Carol — meta: R$ 10.000/mês — carteira: 57 clientes, destaque para Moda Infantil/Bebê e Atacado Têxtil como Vida Baby, Spada, Vigat, Sonho Mágico, Aconchego do Bebê)
M.N REPRESENTACAO COMERCIAL LTDA
CALL REPRESENTACOES TEXTIL LTDA
CINK TEXTIL REPRESENTACOES COMERCIAIS LTDA
CS REPRESENTACOES TEXTEIS LTDA
DESIGNTEX INDUSTRIA E COMERCIO DE TECIDOS LTDA
ADILSON BESERRA LIMA LTDA
ARTE DA MODA TECIDOS E REPRESENTACOES LTDA
BUENO REPRESENTACOES LTDA
C-TEXTIL REPRESENTACOES LTDA
D.S.AGUIAR REPRESENTACOES LTDA
DEBORA CRISTINA CRESPI SIQUEIRA
DIMA REPRESENTACOES LTDA
DOUGLAS NERY CORNELIO E SILVA REPRESENTACOES LTDA
E B LIMA NETO
ELIANE RODRIGUES REPRESENTACOES COMERCIAIS
ESTILO DE PANO COMERCIO E REPRESENTACAO LTDA
F A MOREIRA ASSESSORIA E REPRESENTACOES LTDA
FAC REPRESENTACOES LTDA
FILTEXTIL REPRESENTACOES LTDA
FISCHER & BARBOSA LTDA
GLENIO PEDRINI REPRESENTACOES LTDA
INNOTEX ASSESSORIA TEXTIL LTDA
J A LUIZ DA SILVA REPRESENTACOES
J M TIMBO REPRESENTACOES & PROMOCOES LTDA
JESSICA CARDOSO NADU
JULIANA ARMELIN
LION S ROAR REPRESENTACAO COMERCIAL LTDA
LMK REPRESENTACOES EIRELI
M A BARBOSA DE SOUSA PICANCO REPRESENTACAO
M G BRAND TECIDOS LTDA
MAIA E VIANA REPRESENTACOES LTDA
MARKETING REPRESENTACOES LTDA
MJS CONSULTORIA E GESTAO COMERCIAL EIRELI
N.JACOMEL LTDA
RAIMUNDA VERAS MONTEIRO REP DE TECIDOS
RIS REPRESENTACOES E COMERCIO TEXTEIS LTDA
RR REPRESENTACOES TEXTIL LTDA
RTX REPRESENTACOES LTDA ME
SOTEXTIL COM E REP DE ARTIGOS FUNERARIOS E T
TEXTIL L.DINIZ REPRESENTACOES EIRELI
TFB REPRESENTACOES LTDA
TUAREG REPRESENTACOES LTDA
V G A REPRESENTACOES DE PRODUTOS TEXTEIS LTDA
W.S. CONSULTORIA E REPRESENTACOES COMERCIAIS LTDA
WASHDESIGN . FERES REPRESENTACAO LTDA
ZILMA TEIXEIRA DE LIMA REPRESENTACOES

## MÓDULOS DO PORTAL

/                     - Dashboard com KPIs e gráficos de performance
/meus-pedidos         - Lista de pedidos do TOTVS filtráveis por status, data, cliente
/pedidos/novo         - Criação de pedidos no portal
/pedidos/aprovacoes   - Pedidos aguardando aprovação (gestor)
/clientes             - Cadastro, histórico e mapa de clientes
/estoques             - Consulta de estoque por produto/cor
/programacao          - Previsão de produção e datas de disponibilidade
/tabelas-precos       - Gerenciamento de tabelas de preços (gestor)
/desenvolvimento-exclusivo - Desenvolvimento de cores/artigos exclusivos
/sac                  - Atendimento, reclamações e devoluções
/comissoes            - Extrato de comissões por período
/credito/diretoria    - Análise de crédito de clientes (gestor/diretoria)
/relatorios           - Relatórios gerenciais exportáveis
/financeiro/boletos   - Consulta de boletos e inadimplência
/agenda               - Agendamento de visitas a clientes
/materiais            - Catálogo de materiais de apoio (lookbooks, amostras)
/pcp                  - Planejamento e controle da produção

## PERFIS DE ACESSO

gestor - acesso total a todos os dados de todos os representantes
representante - vê apenas seus próprios pedidos, clientes e metas
diretoria - acesso a crédito, aprovações, financeiro

## VOCABULÁRIO TÊXTIL

metragem = quantidade em metros de tecido
referência = linha de produto (ex: Tricoline Paris, Sarja Prowork)
cor = variação de cor dentro de uma referência (ex: 302 Rosa Pink)
pronto entrega / PE = estoque disponível para entrega imediata
carteira = pedidos em aberto ainda não faturados
faturamento = valor de notas fiscais emitidas (receita realizada)
triangular = venda onde o produto vai direto do fabricante para o cliente final
CIF = frete por conta da Designtex
FOB = frete por conta do comprador
SAC = Serviço de Atendimento ao Cliente
lote = grupo de pedidos processados juntos

## RPCS DO SUPABASE

conexo_vendas_periodo(p_tenant, inicio, fim, p_rep) - resumo: faturado_valor, carteira_valor, faturado_metragem, carteira_metragem, total_pedidos
conexo_relatorio_periodo(p_tenant, inicio, fim) - retorna: resumo, top_clientes, top_produtos, ranking_vendedores, por_regiao
conexo_ranking_vendedores(p_tenant, inicio, fim, p_rep, limite) - colunas: representante_codigo, vendedor, faturamento, metragem_vendida, total_pedidos
conexo_top_clientes(p_tenant, inicio, fim, p_rep, limite) - colunas: cliente, total_pedidos, faturamento, metragem_vendida
conexo_top_produtos(p_tenant, inicio, fim, p_rep, limite) - colunas: produto, metragem, faturamento
conexo_top_cores(p_tenant, inicio, fim, p_rep, limite)
conexo_vendas_regiao(p_tenant, inicio, fim, p_rep)
conexo_comparativo_mes(p_tenant, mes_ref) - compara mês com anterior
conexo_comparativo_ano(p_tenant, inicio, fim) - compara período com ano anterior
conexo_vendedores_abaixo_meta(p_tenant, inicio, fim)
conexo_clientes_inativos(p_tenant, dias_sem_comprar)
conexo_executar_leitura(query_str) - executa SQL SELECT livre (gestor apenas)

## HISTÓRICO DE DADOS

Total de pedidos no banco: 9.058
Período: 2019-09-03 até hoje
Pedidos com nota fiscal: 7.920 (87,4%)
Pedidos sem nota fiscal: 1.138 (12,6%)
