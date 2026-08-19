"""
Job de alertas de mercado — roda semanalmente via cron.
Detecta movimentos de preço nos insumos-chave de cada tenant.
Agende no servidor: 0 12 * * 1 (9h BRT, toda segunda-feira)
"""
from executor import supabase
from mercado.motor import analisar_mercado
from datetime import datetime, timezone


PALAVRAS_ALERTA = ["alta", "queda", "subiu", "caiu", "disparou", "recuo", "avanço"]


def rodar_alertas_mercado():
    tenants = (
        supabase.table("tenants")
        .select("id, perfil_mercado")
        .eq("ativo", True)
        .execute()
        .data
    )
    for t in tenants:
        perfil = t.get("perfil_mercado") or {}
        insumos = perfil.get("insumos_chave", [])[:3]
        ctx = {"tenant_id": t["id"], "rep": None}

        for insumo in insumos:
            try:
                res = analisar_mercado(
                    {
                        "assunto": f"variação de preço {insumo} últimos 7 dias",
                        "cruzar_com_interno": False,
                    },
                    ctx,
                )
                analise_lower = res["analise"].lower()
                if any(k in analise_lower for k in PALAVRAS_ALERTA):
                    supabase.table("conexo_alertas").insert({
                        "tenant_id":  t["id"],
                        "tipo":       "mercado",
                        "severidade": "media",
                        "mensagem": (
                            f"Movimento no insumo '{insumo}': "
                            f"{res['analise'][:200]}"
                        ),
                        "dados":      {"fontes": res.get("fontes", [])[:2]},
                        "lido":       False,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }).execute()
            except Exception as e:
                print(f"[conexo alertas_mercado] insumo '{insumo}' tenant {t['id']}: {e}")


if __name__ == "__main__":
    rodar_alertas_mercado()
    print("Job de alertas de mercado concluído.")
