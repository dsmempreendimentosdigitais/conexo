from fastapi import Header, HTTPException
from executor import supabase


def get_contexto(authorization: str = Header(...)) -> dict:
    """
    Extrai o usuário do token Supabase e devolve seu tenant/perfil.
    O tenant NUNCA vem do corpo da requisição — só do token validado.
    """
    token = authorization.replace("Bearer ", "").strip()
    try:
        user_res = supabase.auth.get_user(token)
        user = user_res.user
        if not user:
            raise ValueError("Usuário não retornado")
    except Exception:
        raise HTTPException(401, "Token inválido ou expirado.")

    resp = (
        supabase.table("conexo_usuarios")
        .select("tenant_id, perfil, representante_codigo, ativo, email, id, auth_user_id")
        .or_(f"auth_user_id.eq.{user.id},id.eq.{user.id},email.eq.{user.email}")
        .execute()
    )

    users = resp.data or []
    u = users[0] if users else None
    if not u or not u.get("ativo"):
        raise HTTPException(403, "Usuário sem acesso ou desativado.")

    perfil = (u.get("perfil") or "gestor").lower()

    return {
        "tenant_id": u["tenant_id"],
        "perfil":    perfil,
        # vendedor → filtra só o dele; gestor / admin / diretoria → None (acesso total a toda a empresa)
        "rep":       u["representante_codigo"] if perfil == "vendedor" else None,
        "email":     u["email"],
    }
