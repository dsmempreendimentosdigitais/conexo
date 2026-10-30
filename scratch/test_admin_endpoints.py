import sys, os
sys.path.insert(0, os.path.abspath("."))
from config import config
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

headers = {"X-Admin-Key": config.ADMIN_KEY}

# 1. Test overview
r_overview = client.get("/conexo/admin/overview", headers=headers)
print("OVERVIEW STATUS:", r_overview.status_code)
print("OVERVIEW DATA:", r_overview.json())

# 2. Test tenants
r_tenants = client.get("/conexo/admin/tenants", headers=headers)
print("\nTENANTS STATUS:", r_tenants.status_code)
for t in r_tenants.json():
    print(f" - Tenant: {t.get('nome')} | Plano: {t.get('plano')} | MRR: R$ {t.get('valor_mensal')} | Conectores: {t.get('conectores_resumo')}")

# 3. Test users
r_users = client.get("/conexo/admin/users", headers=headers)
print("\nUSERS STATUS:", r_users.status_code)
for u in r_users.json():
    print(f" - User: {u.get('email')} | Nome: {u.get('nome')} | Perfil: {u.get('perfil')} | Empresa: {u.get('tenant_nome')}")

# 4. Test financeiro
r_fin = client.get("/conexo/admin/financeiro", headers=headers)
print("\nFINANCEIRO STATUS:", r_fin.status_code)
print("FINANCEIRO DATA:", r_fin.json())
