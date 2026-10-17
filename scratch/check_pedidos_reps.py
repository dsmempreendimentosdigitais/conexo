import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

sql = """
SELECT 
    p.representante_codigo,
    MAX(p.representante_nome) as nome_pedidos,
    r.nome as nome_rep_tabela,
    r.supervisor,
    r.ativo,
    COUNT(*) as total_pedidos,
    SUM(p.valor_total) as faturamento_pedidos
FROM pedidos_totvs p
LEFT JOIN representantes r ON r.codigo = p.representante_codigo
GROUP BY p.representante_codigo, r.nome, r.supervisor, r.ativo
ORDER BY faturamento_pedidos DESC
"""

res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
data = res.data

print(f"Total representative codes in pedidos_totvs: {len(data)}")
print("\n--- Representatives with Sales/Orders ---")
for d in data[:35]:
    code = str(d.get('representante_codigo') or '')
    name = str(d.get('nome_pedidos') or '')[:35]
    sup = str(d.get('supervisor'))
    ativo = str(d.get('ativo'))
    fat = float(d.get('faturamento_pedidos') or 0)
    print(f"Code: {code:>10} | PedidosName: {name:35} | Sup: {sup:10} | Ativo: {ativo:5} | Fat: R$ {fat:12,.2f}")
