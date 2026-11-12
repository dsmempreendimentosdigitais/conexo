import sys
sys.path.append('.')
import re
import unicodedata
from executor import supabase

def desacentuar(txt: str) -> str:
    if not txt:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(txt)) if unicodedata.category(c) != "Mn"
    ).lower().strip()

def detectar_solicitacao_reserva(texto: str):
    t_raw = str(texto or "").strip()
    t_norm = desacentuar(t_raw)

    # 1. Detectar metragem
    match_m = re.search(r'(\d+[\d.,]*)\s*(?:metros?|m\b|mts?)\b', t_norm)
    if not match_m:
        match_m = re.search(r'(?:quero|preciso|reservar|separe|separar|comprar|pedir)\s+(\d+[\d.,]*)', t_norm)
    
    if not match_m:
        return None

    num_str = match_m.group(1).replace(".", "").replace(",", ".")
    try:
        metros = float(num_str)
        if metros <= 0:
            return None
    except:
        return None

    # 2. Extrair termos de busca limpando palavras comuns
    sobra = t_norm
    # Remove a metragem encontrada
    sobra = re.sub(r'(\d+[\d.,]*)\s*(?:metros?|m\b|mts?)\b', ' ', sobra)
    sobra = re.sub(r'\b(quero|preciso|reserva|reservar|separe|separar|comprar|pedir|gostaria|favor|de|da|do|na|no|em|um|uma|uns|umas|o|a|os|as|por|para)\b', ' ', sobra)
    termos = [w.strip() for w in sobra.split() if len(w.strip()) >= 2]

    if not termos:
        return None

    # 3. Buscar correspondência no estoque_pe
    # Tenta montar cláusula com termos
    conds = [f"(descricao ILIKE '%{w}%' OR cor ILIKE '%{w}%' OR cod_produto ILIKE '%{w}%' OR cor_codigo ILIKE '%{w}%')" for w in termos]
    where_termos = " AND ".join(conds)

    sql = f"""
    SELECT cod_produto, descricao, cor, cor_codigo, hex_color, quantidade_disponivel, categoria
    FROM estoque_pe
    WHERE quantidade_disponivel > 0 AND ({where_termos})
    ORDER BY quantidade_disponivel DESC
    LIMIT 1
    """

    try:
        res = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        rows = res.data or []
        if rows:
            return {"metros": metros, "item": rows[0]}
    except Exception as e:
        print("Erro sql:", e)

    return None

testes = [
    "quero 1000 metros de off white na tricoline paris plus",
    "quero 100 metros de tricoline paris off white",
    "preciso de 500 metros de sarja flex bege areia",
    "separe 200m de linho deluxe natural",
    "quero 50 metros de tricoline paris marrom magno"
]

for t in testes:
    res = detectar_solicitacao_reserva(t)
    if res:
        it = res["item"]
        print(f"FRASE: '{t}'")
        print(f" -> Metros: {res['metros']} m | Produto: {it['cod_produto']} - {it['descricao'][:35]} | Cor: {it['cor'][:25]} | Saldo: {it['quantidade_disponivel']} m\n")
    else:
        print(f"FRASE: '{t}' -> NÃO DETECTADO\n")
