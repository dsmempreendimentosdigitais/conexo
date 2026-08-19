import httpx
from config import config

# Fontes confiáveis por setor (amplie conforme o nicho do cliente)
FONTES_CONFIAVEIS = [
    "cepea.esalq.usp.br", "ibge.gov.br", "gov.br", "abit.org.br",
    "valor.globo.com", "reuters.com", "bloomberg.com", "canalrural.com.br",
    "agenciabrasil.ebc.com.br", "cni.com.br", "abimaq.org.br",
]


def buscar_web(query: str, n: int = 5) -> list[dict]:
    """
    Busca web via Tavily com foco em fontes confiáveis.
    Retorna lista de {titulo, trecho, fonte, data}.
    """
    if not config.TAVILY_API_KEY:
        return []   # se não tiver chave, retorna vazio (graceful degradation)

    try:
        r = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key":        config.TAVILY_API_KEY,
                "query":          query,
                "search_depth":   "advanced",
                "max_results":    n,
                "include_domains": FONTES_CONFIAVEIS,
            },
            timeout=20,
        )
        r.raise_for_status()
        dados = r.json().get("results", [])
        return [
            {
                "titulo": d.get("title", ""),
                "trecho": d.get("content", "")[:500],
                "fonte":  d.get("url", ""),
                "data":   d.get("published_date"),
            }
            for d in dados
        ]
    except Exception:
        return []   # nunca derruba a resposta por falha na busca
