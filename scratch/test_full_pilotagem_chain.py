import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from router import rotear
from executor import executar

intent, params = rotear("Tem quantos pedidos de pilotagem em atraso?", "samuel.mc85@gmail.com")
print(f"Roteado para: {intent} com {params}")
dados = executar(intent, params)
print(f"Total pedidos retornados: {len(dados)}")
for d in dados:
    print(f"  Pedido {d.get('pedido')} | Cliente: {d.get('cliente')} | Prev: {d.get('previsao_faturamento')} | Metros: {d.get('metros')} | R$ {d.get('valor_total')}")
