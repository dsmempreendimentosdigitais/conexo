import json
from openai import OpenAI
from config import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

ANALISTA_SYSTEM = """Você é o engenheiro de dados do CONEXO. Recebe o schema \
de um banco de um cliente novo e produz um MAPEAMENTO SEMÂNTICO: identifica \
quais tabelas/colunas correspondem aos conceitos que o CONEXO precisa.

Conceitos que o CONEXO precisa localizar:
- fonte_vendas: tabela principal de pedidos/vendas faturadas
- data_faturamento: coluna de data em que a venda virou receita
- data_pedido: coluna de data em que o pedido entrou
- valor_venda: coluna de valor total do pedido/venda
- status: coluna de situação + quais valores significam "faturado/válido"
- cliente: tabela e chave de clientes
- representante: tabela e chave de vendedores + coluna de meta (se houver)
- itens: onde estão os itens (coluna JSON ou tabela filha) e as chaves de \
  produto, quantidade faturada e preço
- regiao: coluna de UF/estado

REGRAS:
- Baseie-se SÓ no schema fornecido. Não invente colunas.
- Para cada conceito, dê: tabela, coluna e um campo "confianca" (alta/media/baixa).
- Se um conceito NÃO existir no schema, marque como "ausente" e explique o impacto.
- Liste "perguntas_ao_integrador": dúvidas que só um humano do cliente resolve \
  (ex.: quais status contam como faturado).
- Responda SOMENTE em JSON válido.
"""


def analisar_schema(schema_texto: str) -> dict:
    """
    Analisa o schema SQL/texto do cliente e devolve mapeamento semântico.
    Usa o modelo bom (gpt-4o) pois é tarefa de entendimento profundo.
    """
    resp = client.chat.completions.create(
        model=config.MODEL_FORMATTER,
        messages=[
            {"role": "system", "content": ANALISTA_SYSTEM},
            {"role": "user", "content": f"SCHEMA DO CLIENTE:\n{schema_texto}"},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)
