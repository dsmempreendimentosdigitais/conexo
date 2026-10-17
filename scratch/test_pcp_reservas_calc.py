import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Test PCP OP query with reservada calculation
sql = """
SELECT 
    op, 
    nome_tecido, 
    nome_cor, 
    quantidade_solicitada, 
    quantidade_disponivel, 
    GREATEST(0, quantidade_solicitada - quantidade_disponivel) AS quantidade_reservada
FROM programacoes
WHERE quantidade_solicitada > 0
ORDER BY op DESC
LIMIT 15
"""

res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
data = res.data or []
print(f"Total OPs fetched: {len(data)}")
for r in data[:10]:
    sol = r.get('quantidade_solicitada')
    disp = r.get('quantidade_disponivel')
    resv = r.get('quantidade_reservada')
    print(f"OP: {r.get('op'):20} | Tecido: {r.get('nome_tecido'):20} | Cor: {r.get('nome_cor'):15} | Solicitada: {sol:8.1f} | Disponivel: {disp:8.1f} | Reservada: {resv:8.1f}")
