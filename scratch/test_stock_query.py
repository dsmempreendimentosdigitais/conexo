import sys
sys.path.append('.')
from executor import supabase

sql = """
SELECT cod_produto, descricao, cor, cor_codigo, hex_color, quantidade_disponivel 
FROM estoque_pe 
WHERE quantidade_disponivel > 0 
  AND (descricao ILIKE '%tricoline%paris%' OR cod_produto = '1000') 
  AND (cor ILIKE '%off%white%' OR cor_codigo ILIKE '%001%')
ORDER BY quantidade_disponivel DESC 
LIMIT 3
"""
res = supabase.rpc('conexo_executar_leitura', {'query_str': sql}).execute()
print(res.data)
