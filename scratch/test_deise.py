import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
from deise_service import DeiseService

print("--- TESTE 1: BOAS-VINDAS DA DEISE (FOXSTÊXTIL - COD 14) ---")
msg = DeiseService.gerar_boas_vindas("14")
print(msg)

print("\n--- TESTE 2: CONSULTA PRONTA ENTREGA (LINHO LISO) ---")
itens = DeiseService.consultar_estoque_pronta_entrega("liso", "linho")
for it in itens[:3]:
    print(f"Artigo: {it['artigo']} | Cor: {it['cor']} | Saldo: {it['metros_disponiveis']} m")

print("\n--- TESTE 3: TRANSFERÊNCIA PARA REPRESENTANTE ---")
transf = DeiseService.gerar_transferencia_representante("14")
print(transf["mensagem"])
