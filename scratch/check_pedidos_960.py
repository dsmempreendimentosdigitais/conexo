import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

query = """
SELECT 
    p.totvs_order_code,
    p.status,
    item->>'referenceCode' as ref_code,
    item->>'referenceName' as ref_name,
    item->>'colorCode' as color_code,
    item->>'colorName' as color_name,
    item->>'quantity' as quantity
FROM pedidos_totvs p,
LATERAL jsonb_array_elements(
    CASE WHEN jsonb_typeof(p.items_json) = 'array' THEN p.items_json ELSE '[]'::jsonb END
) item
WHERE p.status IN ('InProgress', 'Blocked', 'InComposition')
  AND item->>'colorCode' = '960'
"""

try:
    res = supabase.rpc("conexo_executar_leitura", {"query_str": query}).execute().data
    print(f"TOTAL ORDERS WITH COLOR 960: {len(res)}")
    total_qty = sum(float(r['quantity'] or 0) for r in res)
    print(f"TOTAL SUMMED QUANTITY: {total_qty}")
    print("FIRST 5 ORDERS:")
    print(json.dumps(res[:5], indent=2, ensure_ascii=False))
    
    # Group by ref_code / ref_name
    from collections import defaultdict
    by_prod = defaultdict(float)
    for r in res:
        k = f"{r.get('ref_code')} - {r.get('ref_name')}"
        by_prod[k] += float(r.get('quantity') or 0)
    print("\nGROUPED BY PRODUCT:")
    for k, v in by_prod.items():
        print(f"  {k}: {v} metros")
except Exception as e:
    print("Error:", e)
