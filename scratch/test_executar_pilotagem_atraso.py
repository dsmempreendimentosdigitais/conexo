import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import executar

res = executar("conexo_consulta_pedidos", {"lote": "PIL", "status_filtro": "atrasados"})
print(f"COUNT RETURNED: {len(res) if isinstance(res, list) else res}")
print(json.dumps(res, indent=2, ensure_ascii=False))
