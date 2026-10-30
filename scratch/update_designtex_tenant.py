import sys, os
sys.path.insert(0, os.path.abspath("."))
from executor import supabase

conectores_designtex = {
    "totvs_moda": {
        "ativo": True,
        "tipo": "totvs_moda",
        "nome": "TOTVS Moda (Bhan)",
        "base_url": "https://www30.bhan.com.br:9443/api/totvsmoda",
        "client_id": "designtexapiv2",
        "client_secret": "5871699427",
        "username": "samuel",
        "password": "2025",
        "branch_code": "001",
        "company_code": "01",
        "status": "online",
    },
    "sankhya": {
        "ativo": False,
        "tipo": "sankhya",
        "nome": "Sankhya ERP (API Gateway)",
        "base_url": "https://api.sankhya.com.br/gateway/v1",
        "app_key": "",
        "client_token": "",
        "username": "",
        "password": "",
        "status": "nao_configurado"
    },
    "database": {
        "ativo": True,
        "tipo": "postgresql",
        "nome": "PostgreSQL (Supabase)",
        "host": "liolnupwhhpsryfgnnyl.supabase.co",
        "database": "postgres",
        "status": "online"
    }
}

supabase.table("tenants").update({
    "nome_fantasia": "Designtex Tecidos",
    "plano": "Enterprise",
    "valor_mensal": 3500.00,
    "dia_vencimento": 10,
    "status_pagamento": "em_dia",
    "conectores": conectores_designtex,
    "logo_url": "/logo_icone.png",
    "cor_primaria": "#10a37f"
}).eq("id", "5524e575-2d2f-4753-8bc8-17fe9585ecbc").execute()

print("Designtex tenant updated successfully!")
