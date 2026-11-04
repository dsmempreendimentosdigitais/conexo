import sys, os, json
sys.path.insert(0, os.path.abspath("."))
from router import rotear

intent, params = rotear("Tem quantos pedidos de pilotagem em atraso?", "samuel.mc85@gmail.com")
print("ROUTER INTENT:", intent)
print("ROUTER PARAMS:", json.dumps(params, indent=2, ensure_ascii=False))
