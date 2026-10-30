import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from router import rotear
from executor import executar
from formatter import formatar

pergunta = "verifique os pedidos com lote pedido EXC e sugira quanto preciso programar na fábrica"
usuario = "samuel.mc85@gmail.com"
ctx = {
    "tenant_id": "5524e575-2d2f-4753-8bc8-17fe9585ecbc",
    "perfil": "admin",
    "rep": None,
    "email": usuario,
}

print("1. ROTEAMENTO...")
intent, params = rotear(pergunta, usuario, [])
print("Intent:", intent)
print("Params:", params)

print("\n2. EXECUÇÃO...")
dados = executar(intent, params, ctx)
print("Tipo dados:", type(dados))
if isinstance(dados, list):
    print("Qtd registros retornados:", len(dados))
    total_m = sum(float(d.get("metros") or 0) for d in dados)
    total_v = sum(float(d.get("valor_total") or 0) for d in dados)
    print(f"SOMA TOTAL METRAGEM: {total_m:,.2f} m | SOMA TOTAL VALOR: R$ {total_v:,.2f}")
    if dados:
        print("Primeiro pedido:", dados[0])

print("\n3. FORMATAÇÃO...")
texto = formatar(pergunta, intent, dados)
sys.stdout.reconfigure(encoding='utf-8')
print(texto)
