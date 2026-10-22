import json
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI
from config import config
from prompts import ROUTER_SYSTEM
from tools import TOOLS

client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL, max_retries=1)

def rotear(pergunta: str, usuario: str, historico: list | None = None) -> tuple[str, dict]:
    """
    Roteia a pergunta para a intent correta.
    historico: lista de dicts {"role": "user"|"nexo", "conteudo": str}
    """
    agora = datetime.now(ZoneInfo(config.TIMEZONE))
    system = ROUTER_SYSTEM.format(
        empresa=config.EMPRESA,
        data_atual=agora.strftime("%Y-%m-%d (%A)"),
        usuario=usuario,
    )

    msgs = [{"role": "system", "content": system}]

    # Injeta as últimas 4 trocas como contexto de conversa (memória curta)
    for t in (historico or [])[-4:]:
        papel = "user" if t.get("role") == "user" else "assistant"
        msgs.append({"role": papel, "content": t.get("conteudo", "")})

    msgs.append({"role": "user", "content": pergunta})

    import time
    resp = None
    ultimo_erro = None
    for tentativa in range(3):
        try:
            resp = client.chat.completions.create(
                model=config.MODEL_ROUTER,
                messages=msgs,
                tools=TOOLS,
                tool_choice="required",   # obriga escolher uma ferramenta
                temperature=0,            # roteamento é decisão, não criatividade
            )
            break
        except Exception as e:
            ultimo_erro = e
            if tentativa < 2 and any(code in str(e) for code in ["503", "429", "UNAVAILABLE", "quota", "ResourceExhausted"]):
                time.sleep(2.5 * (tentativa + 1))
                continue
            raise

    if not resp:
        raise ultimo_erro or RuntimeError("Falha no roteamento")

    call = resp.choices[0].message.tool_calls
    if not call:
        return "fora_de_escopo", {"motivo": "não foi possível interpretar"}
    return call[0].function.name, json.loads(call[0].function.arguments or "{}")
