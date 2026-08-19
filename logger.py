from executor import supabase


def log_consulta(usuario: str, pergunta: str, intent: str, params: dict, sucesso: bool):
    """Registra cada consulta na tabela conexo_logs para auditoria."""
    try:
        supabase.table("conexo_logs").insert({
            "usuario":    usuario,
            "pergunta":   pergunta,
            "intent":     intent,
            "parametros": params,
            "sucesso":    sucesso,
        }).execute()
    except Exception:
        pass  # log não pode derrubar a resposta ao usuário
