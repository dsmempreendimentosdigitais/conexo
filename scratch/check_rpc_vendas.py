import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

try:
    res = supabase.table("tenants").select("id, slug, nome").execute().data
    print("TENANTS:", res)
    tenant_id = res[0]["id"]
    res2 = supabase.rpc("conexo_vendas_periodo", {"inicio": "2026-09-01", "fim": "2026-09-30", "p_rep": None, "p_tenant": tenant_id}).execute().data
    print("CONEXO_VENDAS_PERIODO (WHOLE COMPANY):", json.dumps(res2, indent=2))
    
    # And for Michele (p_rep = '3071')
    res3 = supabase.rpc("conexo_vendas_periodo", {"inicio": "2026-09-01", "fim": "2026-09-30", "p_rep": "3071", "p_tenant": tenant_id}).execute().data
    print("CONEXO_VENDAS_PERIODO (MICHELE 3071):", json.dumps(res3, indent=2))
except Exception as e:
    print(e)
