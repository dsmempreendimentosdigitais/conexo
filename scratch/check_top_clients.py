import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from supabase import create_client

sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

sql = """
SELECT cliente_nome, cliente_codigo, COUNT(*) as qtd_pedidos, SUM(valor_total) as faturamento_total, SUM(quantidade_total) as metros_total
FROM pedidos_totvs
WHERE cliente_nome IS NOT NULL AND valor_total > 0
GROUP BY cliente_nome, cliente_codigo
ORDER BY faturamento_total DESC
LIMIT 10
"""

try:
    res = sb.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
    for row in res.data:
        nome = row.get("cliente_nome")
        cod = row.get("cliente_codigo")
        ped = row.get("qtd_pedidos")
        fat = float(row.get("faturamento_total") or 0)
        met = float(row.get("metros_total") or 0)
        print(f"{nome} (Cod: {cod}) -> {ped} pedidos | R$ {fat:,.2f} | {met:,.1f} m")
except Exception as e:
    print("Error:", e)
