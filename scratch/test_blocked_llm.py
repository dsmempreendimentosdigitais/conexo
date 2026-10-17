import sys, os
sys.path.append(os.getcwd())
import json
from openai import OpenAI
from config import config
from prompts import ROUTER_SYSTEM
from tools import TOOLS

client = OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL if config.IS_GEMINI else None
)

def test_question(q):
    print(f"\n==========================================")
    print(f"Testing Question: '{q}'")
    sys_prompt = ROUTER_SYSTEM.format(
        empresa=config.EMPRESA,
        data_atual="2026-09-30",
        usuario="Gestor"
    )
    
    response = client.chat.completions.create(
        model=config.MODEL_ROUTER,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": q}
        ],
        tools=TOOLS,
        tool_choice="auto"
    )
    
    msg = response.choices[0].message
    if msg.tool_calls:
        for tc in msg.tool_calls:
            print(f"Tool Name: {tc.function.name}")
            args = json.loads(tc.function.arguments)
            if tc.function.name == "conexo_consulta_geral":
                sql = args.get("sql", "").strip().rstrip(";")
                print(f"\nGenerated SQL:\n{sql}\n")
                from supabase import create_client
                sp = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                try:
                    res = sp.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
                    print("Supabase Execution Result: SUCCESS! Rows:", len(res.data) if res.data else 0)
                    if res.data:
                        print(f"Total pedidos no header: {res.data[0].get('total_pedidos_geral')} | Valor total: R$ {float(res.data[0].get('valor_total_geral') or 0):,.2f}")
                        print("Sample row:", res.data[0])
                except Exception as err:
                    print("Supabase Execution ERROR:", err)

test_question("Pedidos bloqueados")
test_question("quais pedidos estão bloqueados no portal de vendas?")
