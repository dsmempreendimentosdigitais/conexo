import sys, os, json
from collections import defaultdict, Counter
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from config import config
from supabase import create_client

sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

print("Iniciando extração e mapeamento dos 50 Melhores Clientes...")

# 1. Buscar os Top 50 clientes por faturamento acumulado em pedidos_totvs
sql_top50 = """
SELECT 
    cliente_codigo,
    cliente_nome,
    representante_codigo,
    representante_nome,
    COUNT(*) as total_pedidos,
    SUM(valor_total) as faturamento_total,
    SUM(quantidade_total) as metros_total,
    MIN(data_pedido) as primeiro_pedido,
    MAX(data_pedido) as ultimo_pedido
FROM pedidos_totvs
WHERE cliente_nome IS NOT NULL AND valor_total > 0
GROUP BY cliente_codigo, cliente_nome, representante_codigo, representante_nome
ORDER BY faturamento_total DESC
LIMIT 50
"""

res_top = sb.rpc("conexo_executar_leitura", {"query_str": sql_top50}).execute()
top_clientes = res_top.data or []
print(f"Top 50 clientes recuperados: {len(top_clientes)}")

# 2. Para cada cliente, vamos buscar os itens comprados para entender o perfil de tecidos
mapeamento_completo = []

# Mapeamento geral de artigos para recomendação cruzada
catalogo_bases = {
    "Tricoline": ["TRICOLINE", "CLASSIC", "PARIS"],
    "Linho": ["LINHO", "PANAMA", "BELGA", "CARAIVA", "MARAGOGI", "ATALAIA", "DELUXE"],
    "Sarja": ["SARJA", "DAKOTA", "PROWORK", "BYSKAY", "VELVET", "URBAN", "STREET", "INHOTIM"],
    "Fio Tinto / Listrado": ["FIO TINTO", "LISTRADO", "XADREZ", "CHAMBRAY", "STRIPED"],
    "Viscose / Outros": ["VISCOSE", "VERANO", "FLAME", "MEGA SOFT", "PORTO FINO"]
}

for idx, cli in enumerate(top_clientes, 1):
    cod = cli.get("cliente_codigo")
    nome = cli.get("cliente_nome")
    fat = float(cli.get("faturamento_total") or 0)
    met = float(cli.get("metros_total") or 0)
    ped = int(cli.get("total_pedidos") or 0)
    rep = cli.get("representante_nome") or "-"
    prim = cli.get("primeiro_pedido") or "-"
    ult = cli.get("ultimo_pedido") or "-"

    # Busca até 50 pedidos recentes desse cliente para extrair itens_json
    sql_items = f"""
    SELECT items_json
    FROM pedidos_totvs
    WHERE cliente_codigo = '{cod}' AND items_json IS NOT NULL
    ORDER BY data_pedido DESC
    LIMIT 40
    """
    res_items = sb.rpc("conexo_executar_leitura", {"query_str": sql_items}).execute()
    
    artigos_counter = Counter()
    cores_counter = Counter()
    bases_detectadas = set()

    for row in (res_items.data or []):
        items = row.get("items_json")
        if isinstance(items, list):
            for it in items:
                desc = (it.get("productDescription") or it.get("name") or "").strip().upper()
                cor = (it.get("colorDescription") or it.get("colorName") or "").strip().upper()
                qtd = float(it.get("quantity") or 0)

                if desc:
                    artigos_counter[desc] += qtd
                    for base_nome, termos in catalogo_bases.items():
                        if any(t in desc for t in termos):
                            bases_detectadas.add(base_nome)
                if cor:
                    cores_counter[cor] += qtd

    top_artigos = [f"{art} ({qtd:,.0f} m)" for art, qtd in artigos_counter.most_common(3)]
    top_cores = [f"{cor} ({qtd:,.0f} m)" for cor, qtd in cores_counter.most_common(3)]

    # Determinar produtos que o cliente PODERIA comprar (Oportunidades de Cross-Sell)
    bases_nao_compradas = [b for b in ["Tricoline", "Linho", "Sarja", "Fio Tinto / Listrado"] if b not in bases_detectadas]
    if not bases_nao_compradas:
        recomendacao = "Expansão de mix de cores e novos lançamentos de alta gramatura"
    else:
        recomendacao = f"Apresentar lançamentos de: {', '.join(bases_nao_compradas[:2])}"

    ticket_medio = fat / ped if ped > 0 else 0
    preco_medio_metro = fat / met if met > 0 else 0

    perfil = {
        "posicao": idx,
        "codigo": cod,
        "nome": nome,
        "representante": rep,
        "faturamento_total": fat,
        "metros_total": met,
        "total_pedidos": ped,
        "ticket_medio": ticket_medio,
        "preco_medio_m": preco_medio_metro,
        "primeiro_pedido": prim,
        "ultimo_pedido": ult,
        "bases_compradas": list(bases_detectadas) if bases_detectadas else ["Tecidos Gerais"],
        "top_artigos": top_artigos if top_artigos else ["Itens diversos"],
        "top_cores": top_cores if top_cores else ["Cores diversas"],
        "recomendacao_deise": recomendacao
    }
    mapeamento_completo.append(perfil)
    if idx % 10 == 0 or idx == 1:
        print(f"Processado: #{idx} - {nome[:30]} | R$ {fat:,.2f}")

# Salva arquivo JSON estruturado
out_json = "scratch/top50_clientes_analisados.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(mapeamento_completo, f, ensure_ascii=False, indent=2)

print(f"Mapeamento concluído com sucesso e salvo em {out_json}!")
