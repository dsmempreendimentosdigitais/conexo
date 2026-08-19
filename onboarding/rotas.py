from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from config import config
from onboarding.analista import analisar_schema
from onboarding.gerador import gerar_rpcs
from executor import supabase

router = APIRouter(prefix="/conexo/onboarding", tags=["onboarding"])


def somente_admin(x_admin_key: str = Header(...)):
    """Só o admin CONEXO acessa esses endpoints — nunca o cliente."""
    if x_admin_key != config.ADMIN_KEY:
        raise HTTPException(403, "Acesso restrito ao admin CONEXO.")


# ---------- 1. Analisar schema ----------
class SchemaIn(BaseModel):
    cnpj: str
    schema_texto: str


@router.post("/analisar", dependencies=[Depends(somente_admin)])
def analisar(body: SchemaIn):
    """
    Passo 1: IA analisa o schema e devolve mapeamento semântico.
    Não gera nada ainda — aguarda revisão humana.
    """
    mapa = analisar_schema(body.schema_texto)
    supabase.table("conexo_onboarding").upsert(
        {"cnpj": body.cnpj, "mapeamento": mapa, "status": "aguardando_revisao"},
        on_conflict="cnpj",
    ).execute()
    return {
        "cnpj": body.cnpj,
        "mapeamento": mapa,
        "proximo_passo": (
            "Revise o mapeamento, responda as 'perguntas_ao_integrador' "
            "e chame /conexo/onboarding/gerar com o mapeamento corrigido."
        ),
    }


# ---------- 2. Gerar RPCs (após revisão humana) ----------
class GerarIn(BaseModel):
    cnpj: str
    mapeamento_revisado: dict


@router.post("/gerar", dependencies=[Depends(somente_admin)])
def gerar(body: GerarIn):
    """
    Passo 2: IA gera as 10 RPCs SQL a partir do mapeamento revisado.
    ⚠️ VOCÊ ainda deve revisar o SQL e aplicar manualmente no banco.
    """
    resultado = gerar_rpcs(body.mapeamento_revisado)
    supabase.table("conexo_onboarding").update({
        "mapeamento":     body.mapeamento_revisado,
        "rpcs_geradas":   resultado,
        "status":         "rpcs_geradas",
        "updated_at":     "NOW()",
    }).eq("cnpj", body.cnpj).execute()
    return {
        "cnpj":    body.cnpj,
        "rpcs":    resultado["rpcs"],
        "avisos":  resultado.get("avisos", []),
        "proximo_passo": (
            "⚠️ REVISE o SQL. Aplique manualmente no banco do cliente. "
            "Depois teste contra um relatório oficial."
        ),
    }
