import sys
sys.path.insert(0, '.')
from executor import executar
from formatter import formatar

sql = """SELECT rep.nome AS representante_nome, rep.codigo AS representante_codigo, rep.supervisor, rep.meta, p.cliente_nome, COUNT(p.totvs_order_code) AS qtd_pedidos_cliente, ROUND(SUM(COALESCE(p.valor_nf, p.valor_total))::numeric, 2) AS total_comprado, MIN(p.data_pedido::date) AS primeiro_pedido, MAX(p.data_pedido::date) AS ultimo_pedido, COUNT(*) OVER() AS total_clientes_carteira, ROUND(SUM(COALESCE(p.valor_nf, p.valor_total)) OVER()::numeric, 2) AS faturamento_total_representante FROM pedidos_totvs p INNER JOIN representantes rep ON rep.codigo = p.representante_codigo WHERE (rep.nome ILIKE '%Fernandes%' OR rep.nome ILIKE '%Andre%' OR rep.codigo = '3019') AND p.status IN ('Attended', 'PartiallyAnswered', 'InProgress', 'Blocked') AND COALESCE(p.valor_nf, p.valor_total) > 0 GROUP BY rep.nome, rep.codigo, rep.supervisor, rep.meta, p.cliente_nome ORDER BY total_comprado DESC LIMIT 50;"""

dados = executar('conexo_consulta_geral', {'sql': sql}, {'perfil': 'gestor'})
print('Qtd linhas dados:', len(dados))
print('Linha 1:', dados[0] if dados else 'Vazio')

q = 'Qual potencial de crescimento das vendas do representante André levando em consideração o histórico de vendas dele, tamanho dos clientes e o nicho deles, e se poderia aumentar a expectativa de vendas desse representante. E quais planos de ação a designtex precisa executar para dar assistência a ele.'
texto = formatar(q, 'conexo_consulta_geral', dados)
print('--- FORMATTER RESULT ---')
print(texto)
