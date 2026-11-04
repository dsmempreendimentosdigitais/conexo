import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

q1 = """
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'pedido_itens'
"""

q2 = """
SELECT * 
FROM pedido_itens 
WHERE pedido_id = 1732 OR pedido_id = 41732
"""

try:
    r1 = supabase.rpc("conexo_executar_leitura", {"query_str": q1}).execute().data
    print("COLUMNS IN pedido_itens:")
    for r in r1:
        print(f"  {r['column_name']} ({r['data_type']})")

    r2 = supabase.rpc("conexo_executar_leitura", {"query_str": q2}).execute().data
    print("\nROWS IN pedido_itens FOR 1732:")
    print(json.dumps(r2, indent=2, ensure_ascii=False))
except Exception as e:
    print("Error:", e)
