import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

q = "SELECT totvs_order_code, items_json IS NULL as items_json_null, raw_totvs IS NOT NULL as has_raw FROM pedidos_totvs WHERE totvs_order_code = '37249'"
try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": q}).execute().data
    print(json.dumps(res, indent=2))
except Exception as e:
    print(e)
