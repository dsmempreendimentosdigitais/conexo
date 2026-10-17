import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

reps = supabase.table('representantes').select('*').execute().data

with_sup = [r for r in reps if r.get('supervisor') and str(r.get('supervisor')).strip()]
without_sup = [r for r in reps if not (r.get('supervisor') and str(r.get('supervisor')).strip())]

print(f"Total reps in 'representantes' table: {len(reps)}")
print(f"With supervisor: {len(with_sup)}")
print(f"Without supervisor: {len(without_sup)}")

print("\n--- WITH SUPERVISOR breakdown ---")
active_with_sup = [r for r in with_sup if r.get('ativo')]
inactive_with_sup = [r for r in with_sup if not r.get('ativo')]
print(f"Active with supervisor: {len(active_with_sup)}")
print(f"Inactive with supervisor: {len(inactive_with_sup)}")

totvs_with_sup = [r for r in with_sup if 'TOTVS' in r.get('nome', '')]
print(f"TOTVS named with supervisor: {len(totvs_with_sup)}")
for r in totvs_with_sup:
    print(r)

print("\n--- WITHOUT SUPERVISOR breakdown ---")
active_without_sup = [r for r in without_sup if r.get('ativo')]
inactive_without_sup = [r for r in without_sup if not r.get('ativo')]
print(f"Active without supervisor: {len(active_without_sup)}")
print(f"Inactive without supervisor: {len(inactive_without_sup)}")
totvs_without_sup = [r for r in without_sup if 'TOTVS' in r.get('nome', '')]
print(f"TOTVS named without supervisor: {len(totvs_without_sup)}")

