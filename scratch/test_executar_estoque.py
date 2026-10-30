import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from executor import executar

res = executar("conexo_consulta_estoque", {"produto": "tricoline paris", "cor": "marinho noite"})
print("EXECUTAR RESULT:")
print(json.dumps(res, indent=2, ensure_ascii=False))
