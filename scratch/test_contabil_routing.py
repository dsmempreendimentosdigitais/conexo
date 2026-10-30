import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from router import rotear
from executor import executar
from formatter import formatar

pergunta = "o saldo contábil de estoque não é valorizado?"
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
print("Dados tipo:", type(dados))
if isinstance(dados, list):
    print("Qtd registros:", len(dados))
    if dados:
        print("Primeiro registro:", dados[0])

print("\n3. FORMATAÇÃO...")
texto = formatar(pergunta, intent, dados)
sys.stdout.reconfigure(encoding='utf-8')
print(texto)
