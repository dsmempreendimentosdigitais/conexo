import sys
sys.path.insert(0, '.')
from executor import supabase

r_est = supabase.rpc('conexo_executar_leitura', {
    'query_str': "SELECT cod_produto, descricao, cor, cor_codigo, quantidade_disponivel, estoque_1 FROM estoque_pe ORDER BY quantidade_disponivel DESC LIMIT 5"
}).execute()
print("ESTOQUE_PE:", r_est.data)

r_ped = supabase.rpc('conexo_executar_leitura', {
    'query_str': "SELECT item FROM pedidos_totvs p CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(p.items_json) = 'array' THEN p.items_json ELSE '[]'::jsonb END) AS item WHERE p.status IN ('Attended', 'PartiallyAnswered') LIMIT 3"
}).execute()
print("ITEMS_JSON:", r_ped.data)

r_logs = supabase.rpc('conexo_executar_leitura', {
    'query_str': "SELECT pergunta, intent, parametros FROM conexo_logs ORDER BY created_at DESC LIMIT 5"
}).execute()
print("RECENT LOGS:", r_logs.data)
