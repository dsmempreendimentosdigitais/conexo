import json
from openai import OpenAI
from config import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

GERADOR_SYSTEM = """Você é o gerador de RPCs do CONEXO. Recebe um MAPEAMENTO \
SEMÂNTICO já validado por um humano e gera as 10 funções SQL (PostgreSQL/Supabase) \
padrão do CONEXO, adaptadas às tabelas e colunas REAIS daquele mapeamento.

As 10 RPCs (mesma assinatura padrão do CONEXO):
1. conexo_vendas_periodo(p_tenant, inicio, fim)
2. conexo_comparativo_mes(p_tenant, mes_ref)
3. conexo_comparativo_ano(p_tenant, inicio, fim)
4. conexo_ranking_vendedores(p_tenant, p_rep, inicio, fim, limite)
5. conexo_vendedores_abaixo_meta(p_tenant, inicio, fim)
6. conexo_top_produtos(p_tenant, inicio, fim, limite)
7. conexo_top_clientes(p_tenant, p_rep, inicio, fim, limite)
8. conexo_clientes_inativos(p_tenant, dias_sem_comprar)
9. conexo_vendas_regiao(p_tenant, inicio, fim)
10. conexo_relatorio_periodo(p_tenant, inicio, fim)

REGRAS INEGOCIÁVEIS:
- Use APENAS as tabelas/colunas do mapeamento. NUNCA invente nomes.
- TODA RPC filtra por tenant_id = p_tenant (isolamento multi-tenant).
- Vendas por data_faturamento; status conforme os valores validados.
- Todas 'security definer' e 'stable'.
- Se um conceito estava 'ausente' no mapeamento, gere a RPC mesmo assim mas \
  adicione um comentário SQL "-- ⚠️ AJUSTAR: <motivo>" na linha afetada.
- Para itens em JSON, use jsonb_array_elements com as chaves reais mapeadas.
- Para itens em tabela filha, use JOIN.
- Devolva JSON: {"rpcs": [{"nome", "sql", "observacoes"}], "avisos": [...]}
"""


def gerar_rpcs(mapeamento: dict) -> dict:
    """
    Gera as 10 RPCs SQL adaptadas ao schema real do cliente.
    Só deve rodar APÓS revisão humana do mapeamento.
    """
    resp = client.chat.completions.create(
        model=config.MODEL_FORMATTER,
        messages=[
            {"role": "system", "content": GERADOR_SYSTEM},
            {"role": "user", "content": "MAPEAMENTO VALIDADO:\n" +
             json.dumps(mapeamento, ensure_ascii=False, indent=2)},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)
