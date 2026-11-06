import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from supabase import create_client

sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

sql = """
SELECT cliente_nome, items_json
FROM pedidos_totvs
WHERE cliente_codigo = '14' AND items_json IS NOT NULL
LIMIT 3
"""
try:
    res = sb.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
    for row in res.data:
        print("Cliente:", row['cliente_nome'])
        items = row['items_json']
        if isinstance(items, list) and len(items) > 0:
            print("  Item sample:", items[0].get('productDescription') or items[0].get('name'), "| Qtd:", items[0].get('quantity'))
except Exception as e:
    print("Error:", e)
