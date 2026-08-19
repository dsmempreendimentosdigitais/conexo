from fastapi import Header, HTTPException
from executor import supabase


def get_contexto(authorization: str = Header(...)) -> dict:
    """
    Extrai o usuário do token Supabase e devolve seu tenant/perfil.
    O tenant NUNCA vem do corpo da requisição — só do token validado.
    """
    token = authorization.replace("Bearer ", "")
    try:
        user = supabase.auth.get_user(token).user
    except Exception:
        raise HTTPException(401, "Token inválido ou expirado.")

    resp = (
        supabase.table("conexo_usuarios")
        .select("tenant_id, perfil, representante_codigo, ativo, email")
        .eq("auth_user_id", user.id)
        .single()
        .execute()
    )

    u = resp.data
    if not u or not u["ativo"]:
        raise HTTPException(403, "Usuário sem acesso ou desativado.")

    return {
        "tenant_id": u["tenant_id"],
        "perfil":    u["perfil"],
        # vendedor → filtra só o dele; gestor → None (vê tudo)
        "rep":       u["representante_codigo"] if u["perfil"] == "vendedor" else None,
        "email":     u["email"],
    }
