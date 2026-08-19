import json
from openai import OpenAI
from config import config
from prompts import FORMATTER_SYSTEM

client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)


def formatar(pergunta: str, intent: str, dados) -> str:
    # Inteligência de mercado já vem formatada com fontes
    if intent == "conexo_inteligencia_mercado" and isinstance(dados, dict):
        texto = dados.get("analise", "")
        fontes = dados.get("fontes", [])
        if fontes:
            texto += "\n\n**Fontes:**\n" + "\n".join(
                f"- [{f['titulo']}]({f['fonte']})" +
                (f" ({f['data']})" if f.get("data") else "")
                for f in fontes
            )
        return texto

    if not dados:
        return (
            "Não encontrei registros para esse período. "
            "Confira as datas ou tente outro intervalo."
        )

    prompt = FORMATTER_SYSTEM.format(
        empresa=config.EMPRESA,
        pergunta=pergunta,
        intent=intent,
        dados=json.dumps(dados, ensure_ascii=False, indent=2, default=str),
    )
    resp = client.chat.completions.create(
        model=config.MODEL_FORMATTER,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return resp.choices[0].message.content
