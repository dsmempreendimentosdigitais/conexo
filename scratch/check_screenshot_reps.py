import sys, os
sys.path.append(os.getcwd())
from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

names = [
    "LION S ROAR REPRESENTACAO COMERCIAL LTDA",
    "REPRESENTANTE TOTVS #432",
    "I.B.O. REPRESENTACOES LTDA",
    "M A BARBOSA DE SOUSA PICANCO REPRESENTACAO",
    "REPRESENTANTE TOTVS #4277",
    "62.980.353 PEDRO HENRIQUE SILVEIRA COLNAGHI",
    "MORITZ REPRESENTACOES LTDA",
    "REPRESENTANTE TOTVS #1834",
    "M G BRAND TECIDOS LTDA"
]

reps = supabase.table('representantes').select('*').execute().data

for name in names:
    matches = [r for r in reps if name.lower() in r.get('nome', '').lower()]
    if matches:
        for m in matches:
            print(f"Name: {m['nome']} | Sup: {m.get('supervisor')} | Ativo: {m.get('ativo')} | Cod: {m.get('codigo')}")
    else:
        print(f"NOT FOUND in representantes table: {name}")
