import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import config
from supabase import create_client

sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# 1. Log da consulta
print("=== 1. LOGS RECENTES CONEXO ===")
logs = sb.table("conexo_logs").select("*").order("created_at", desc=True).limit(10).execute().data
for l in logs:
    perg = str(l.get("pergunta") or "")
    if "EXC" in perg or "programar" in perg or "lote" in perg:
        print("PERGUNTA:", perg)
        print("INTENT:", l.get("intent"))
        print("PARAMS:", l.get("parametros"))
        print("CRIADO EM:", l.get("created_at"))
        print("---")

# 2. pedidos_totvs com lote_pedido
print("\n=== 2. PEDIDOS_TOTVS (LOTE_PEDIDO) ===")
sql1 = """
SELECT 
    COALESCE(lote_pedido, 'NULO') as lote,
    status, 
    count(*) as qtd_pedidos, 
    ROUND(sum(quantidade_total)::numeric, 1) as metros, 
    ROUND(sum(valor_total)::numeric, 2) as valor
FROM pedidos_totvs
WHERE status IN ('InProgress', 'Blocked', 'Attended', 'PartiallyAnswered')
GROUP BY lote_pedido, status
ORDER BY count(*) DESC
LIMIT 20
"""
res1 = sb.rpc("conexo_executar_leitura", {"query_str": sql1.strip()}).execute().data
for r in res1:
    print(r)

# 3. pedidos_totvs com status Em andamento ou Blocked onde lote_pedido = 'EXC'
print("\n=== 3. PEDIDOS_TOTVS COM LOTE 'EXC' OU SIMILAR ===")
sql2 = """
SELECT 
    count(*) as total_pedidos,
    ROUND(sum(quantidade_total)::numeric, 1) as total_metros,
    ROUND(sum(valor_total)::numeric, 2) as total_valor
FROM pedidos_totvs
WHERE (lote_pedido ILIKE '%EXC%' OR items_json::text ILIKE '%"batchOrder":"EXC"%' OR items_json::text ILIKE '%"lote":"EXC"%')
  AND status IN ('InProgress', 'Blocked')
"""
res2 = sb.rpc("conexo_executar_leitura", {"query_str": sql2.strip()}).execute().data
for r in res2:
    print(r)

# 4. pedidos do Portal (tabela pedidos)
print("\n=== 4. PEDIDOS DO PORTAL (TABELA pedidos) ===")
sql3 = """
SELECT 
    p.status,
    p.tipo_pedido,
    count(*) as qtd,
    ROUND(sum(p.valor_total)::numeric, 2) as valor
FROM pedidos p
WHERE p.status IN ('Em andamento', 'Bloqueado', 'Em composição', 'Em análise')
GROUP BY p.status, p.tipo_pedido
"""
res3 = sb.rpc("conexo_executar_leitura", {"query_str": sql3.strip()}).execute().data
for r in res3:
    print(r)
