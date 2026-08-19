"""
Job de alertas internos — roda diariamente via cron.
Detecta quedas de faturamento e clientes inativos via RPC conexo_detectar_alertas.
Agende no servidor: 0 11 * * * (8h BRT)
"""
from executor import supabase
from datetime import datetime, timezone


def rodar_alertas():
    tenants = (
        supabase.table("tenants")
        .select("id")
        .eq("ativo", True)
        .execute()
        .data
    )
    for t in tenants:
        try:
            alertas = (
                supabase.rpc("conexo_detectar_alertas", {"p_tenant": t["id"]})
                .execute()
                .data
            )
            for a in alertas or []:
                supabase.table("conexo_alertas").insert({
                    "tenant_id":  t["id"],
                    "tipo":       a["tipo"],
                    "severidade": a["severidade"],
                    "mensagem":   a["mensagem"],
                    "dados":      a.get("dados"),
                    "lido":       False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }).execute()
        except Exception as e:
            print(f"[conexo alertas] erro no tenant {t['id']}: {e}")


if __name__ == "__main__":
    rodar_alertas()
    print("Job de alertas internos concluído.")
