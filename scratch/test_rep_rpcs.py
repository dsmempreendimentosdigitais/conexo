import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

print("--- Testing conexo_ranking_vendedores ---")
res1 = supabase.rpc("conexo_ranking_vendedores", {"p_tenant": "5524e575-2d2f-4753-8bc8-17fe9585ecbc", "inicio": "2026-09-01", "fim": "2026-09-25"}).execute()
print("Ranking result:", res1.data)

print("\n--- Testing conexo_vendedores_abaixo_meta ---")
res2 = supabase.rpc("conexo_vendedores_abaixo_meta", {"p_tenant": "5524e575-2d2f-4753-8bc8-17fe9585ecbc", "inicio": "2026-09-01", "fim": "2026-09-25"}).execute()
print("Abaixo meta result:", res2.data[:5] if res2.data else res2.data)
