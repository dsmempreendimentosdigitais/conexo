import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from router import rotear
from executor import executar
from formatter import formatar

pergunta = "desses pedidos de hoje que ainda estão bloqueados. qual é o maior cliente e que poderia já ter o crédito liberado?"
usuario = "samuel.mc85@gmail.com"
ctx = {
    "tenant_id": "5524e575-2d2f-4753-8bc8-17fe9585ecbc",
    "perfil": "admin",
    "rep": None,
    "email": usuario,
}

print("1. Testando roteamento...")
intent, params = rotear(pergunta, usuario, [])
print("Intent:", intent)
print("Params:", params)

print("\n2. Testando execução...")
dados = executar(intent, params, ctx)
print("Dados retornados:", len(dados) if isinstance(dados, list) else type(dados))
if isinstance(dados, list) and dados:
    print("Primeiro registro:", dados[0])

print("\n3. Testando formatação...")
texto = formatar(pergunta, intent, dados)
print("\nRESPOSTA FINAL GERADA:")
sys.stdout.reconfigure(encoding='utf-8')
print(texto)
