import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

reps = supabase.table('representantes').select('*').execute().data

with_supervisor = [r for r in reps if r.get('supervisor') and r.get('supervisor').strip()]
without_supervisor = [r for r in reps if not (r.get('supervisor') and r.get('supervisor').strip())]

print(f"Total reps: {len(reps)}")
print(f"Reps WITH supervisor: {len(with_supervisor)}")
print(f"Reps WITHOUT supervisor: {len(without_supervisor)}")

supervisors = set(r.get('supervisor') for r in with_supervisor)
print(f"Supervisors found: {supervisors}")

print("\nSample reps with supervisor:")
for r in with_supervisor[:10]:
    print(f"Codigo: {r['codigo']}, Nome: {r['nome']}, Supervisor: {r['supervisor']}, Ativo: {r['ativo']}")

print("\nSample reps WITHOUT supervisor:")
for r in without_supervisor[:15]:
    print(f"Codigo: {r['codigo']}, Nome: {r['nome']}, Supervisor: {r['supervisor']}, Ativo: {r['ativo']}")
