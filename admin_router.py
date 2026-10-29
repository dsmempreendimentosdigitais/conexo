import time
import secrets
import string
import datetime
import httpx
from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from config import config
from executor import supabase

router = APIRouter(prefix="/conexo/admin", tags=["Admin CONEXO"])


# ─────────────────────────────────────────────────
# Autenticação de Administrador Master
# ─────────────────────────────────────────────────

def require_admin(
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
) -> dict:
    # 1. Autenticação via Chave Master de Administrador
    if x_admin_key and isinstance(x_admin_key, str) and x_admin_key.strip() == config.ADMIN_KEY:
        return {"is_admin": True, "email": "master@conexo.dev", "perfil": "admin"}

    # 2. Autenticação via Token Supabase com perfil 'admin'
    if not authorization or not isinstance(authorization, str):
        raise HTTPException(401, "Acesso restrito. Forneça o token de login ou a chave X-Admin-Key.")

    token = authorization.replace("Bearer ", "").strip()
    try:
        user_res = supabase.auth.get_user(token)
        user = user_res.user
        if not user:
            raise ValueError("Usuário não retornado pelo Supabase")
    except Exception:
        raise HTTPException(401, "Sessão inválida ou expirada.")

    try:
        # Busca no conexo_usuarios pelo auth_user_id ou pelo id ou pelo email
        res = (
            supabase.table("conexo_usuarios")
            .select("id, email, perfil, tenant_id, ativo, auth_user_id")
            .or_(f"auth_user_id.eq.{user.id},id.eq.{user.id},email.eq.{user.email}")
            .execute()
        )
        users = res.data or []
        u = users[0] if users else None

        if not u or not u.get("ativo"):
            raise HTTPException(403, "Usuário desativado ou sem acesso ao CONEXO.")
        if u.get("perfil") != "admin" or u.get("email") != "conexo.dev.ai@gmail.com":
            raise HTTPException(403, "Apenas o Administrador Master (conexo.dev.ai@gmail.com) tem permissão para acessar o painel master.")
        return u
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(403, f"Erro ao verificar permissão administrativa: {e}")


# ─────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────

class TenantCreateIn(BaseModel):
    nome: str
    nome_fantasia: Optional[str] = None
    cnpj: str
    plano: Optional[str] = "Enterprise"
    valor_mensal: Optional[float] = 3500.00
    dia_vencimento: Optional[int] = 10
    status_pagamento: Optional[str] = "em_dia"
    cor_primaria: Optional[str] = "#38bdf8"
    logo_url: Optional[str] = None
    nicho: Optional[str] = None
    setor: Optional[str] = None
    contrato: Optional[Dict[str, Any]] = None
    conectores: Optional[Dict[str, Any]] = None

class TenantUpdateIn(BaseModel):
    nome: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    plano: Optional[str] = None
    valor_mensal: Optional[float] = None
    dia_vencimento: Optional[int] = None
    status_pagamento: Optional[str] = None
    cor_primaria: Optional[str] = None
    logo_url: Optional[str] = None
    ativo: Optional[bool] = None
    contrato: Optional[Dict[str, Any]] = None
    conectores: Optional[Dict[str, Any]] = None

class ConnectorsSaveIn(BaseModel):
    conectores: Dict[str, Any]

class ConnectorTestIn(BaseModel):
    tipo: str  # "totvs_moda" | "sankhya" | "database"
    config: Dict[str, Any]

class UserCreateIn(BaseModel):
    tenant_id: str
    email: str
    nome: Optional[str] = None
    perfil: Optional[str] = "gestor"  # admin | gestor | supervisor | vendedor
    setor: Optional[str] = None
    representante_codigo: Optional[str] = None
    senha: Optional[str] = None  # se vazio, gera provisória

class UserUpdateIn(BaseModel):
    nome: Optional[str] = None
    perfil: Optional[str] = None
    setor: Optional[str] = None
    representante_codigo: Optional[str] = None
    ativo: Optional[bool] = None
    tenant_id: Optional[str] = None

class ResetPasswordIn(BaseModel):
    nova_senha: Optional[str] = None


# ─────────────────────────────────────────────────
# Rotas: Visão Geral e Métricas SaaS
# ─────────────────────────────────────────────────

@router.get("/overview")
def get_overview(admin=Depends(require_admin)):
    # 1. Tenants e MRR
    tenants_res = supabase.table("tenants").select("*").execute()
    tenants = tenants_res.data or []
    
    mrr_total = sum(float(t.get("valor_mensal") or 0) for t in tenants if t.get("ativo"))
    tenants_ativos = sum(1 for t in tenants if t.get("ativo"))

    # 2. Usuários
    users_res = supabase.table("conexo_usuarios").select("id, ativo").execute()
    users = users_res.data or []
    usuarios_ativos = sum(1 for u in users if u.get("ativo"))

    # 3. Perguntas e Atividade no Mês (conexo_logs)
    hoje = datetime.date.today()
    inicio_mes = hoje.replace(day=1).isoformat()
    
    total_perguntas = 0
    perguntas_mes = 0
    erros_mes = 0
    try:
        res_logs = supabase.rpc("conexo_executar_leitura", {
            "query_str": f"""
            SELECT 
                COUNT(*) as total_geral,
                COUNT(CASE WHEN created_at >= '{inicio_mes}' THEN 1 END) as total_mes,
                COUNT(CASE WHEN created_at >= '{inicio_mes}' AND sucesso IS FALSE THEN 1 END) as erros_mes
            FROM conexo_logs
            """
        }).execute()
        if res_logs.data:
            total_perguntas = int(res_logs.data[0].get("total_geral") or 0)
            perguntas_mes = int(res_logs.data[0].get("total_mes") or 0)
            erros_mes = int(res_logs.data[0].get("erros_mes") or 0)
    except Exception:
        pass

    # Estimativa de Custo de IA (Gemini 2.5 Flash / Whisper: ~R$ 0,02 por consulta completa)
    custo_ia_estimado = round(perguntas_mes * 0.021, 2)
    margem_lucro = round(((mrr_total - custo_ia_estimado) / mrr_total * 100), 1) if mrr_total > 0 else 100.0

    return {
        "mrr_total": mrr_total,
        "lucro_estimado": round(mrr_total - custo_ia_estimado, 2),
        "margem_lucro_pct": margem_lucro,
        "custo_ia_mes": custo_ia_estimado,
        "tenants_total": len(tenants),
        "tenants_ativos": tenants_ativos,
        "usuarios_total": len(users),
        "usuarios_ativos": usuarios_ativos,
        "perguntas_total": total_perguntas,
        "perguntas_mes": perguntas_mes,
        "erros_mes": erros_mes,
        "taxa_sucesso_pct": round(100 - (erros_mes / max(1, perguntas_mes) * 100), 1),
    }


# ─────────────────────────────────────────────────
# Rotas: Gestão de Tenants (Empresas Clientes)
# ─────────────────────────────────────────────────

@router.get("/tenants")
def list_tenants(admin=Depends(require_admin)):
    res = supabase.table("tenants").select("*").order("created_at", desc=False).execute()
    tenants = res.data or []

    # Conta usuários por tenant
    users_res = supabase.table("conexo_usuarios").select("tenant_id, id, ativo").execute()
    users_map = {}
    for u in users_res.data or []:
        tid = u.get("tenant_id")
        if tid not in users_map:
            users_map[tid] = {"total": 0, "ativos": 0}
        users_map[tid]["total"] += 1
        if u.get("ativo"):
            users_map[tid]["ativos"] += 1

    for t in tenants:
        tid = t.get("id")
        t["usuarios"] = users_map.get(tid, {"total": 0, "ativos": 0})
        # Resumo de conectores configurados
        conns = t.get("conectores") or {}
        t["conectores_resumo"] = {
            "totvs_ativo": bool(conns.get("totvs_moda", {}).get("ativo")),
            "sankhya_ativo": bool(conns.get("sankhya", {}).get("ativo")),
            "db_ativo": bool(conns.get("database", {}).get("ativo")),
        }

    return tenants


@router.post("/tenants")
def create_tenant(dados: TenantCreateIn, admin=Depends(require_admin)):
    perfil_mercado = {
        "nicho": dados.nicho or "indústria e confecção",
        "setor": dados.setor or "têxtil",
    }
    
    payload = {
        "nome": dados.nome.strip(),
        "nome_fantasia": (dados.nome_fantasia or dados.nome).strip(),
        "cnpj": dados.cnpj.strip(),
        "plano": dados.plano or "Enterprise",
        "valor_mensal": dados.valor_mensal or 3500.00,
        "dia_vencimento": dados.dia_vencimento or 10,
        "status_pagamento": dados.status_pagamento or "em_dia",
        "cor_primaria": dados.cor_primaria or "#38bdf8",
        "logo_url": dados.logo_url,
        "perfil_mercado": perfil_mercado,
        "ativo": True,
        "contrato": dados.contrato or {
            "numero_contrato": f"DSM-CNX-{datetime.date.today().strftime('%Y')}/{secrets.token_hex(2).upper()}",
            "contratada_razao": "DSM Empreendimentos Digitais Ltda",
            "produto": "CONEXO.dev - Inteligência Comercial com IA",
            "data_inicio": datetime.date.today().strftime("%Y-%m-%d"),
            "vigencia_meses": 12,
            "renovacao_automatica": True,
            "valor_mensal": dados.valor_mensal or 3500.00,
            "dia_vencimento": dados.dia_vencimento or 10,
            "sla_garantido": "99.5%",
            "termos_lgpd": True,
            "suporte_nivel": "Prioritário WhatsApp + Chamados",
        },
        "conectores": dados.conectores or {}
    }
    
    res = supabase.table("tenants").insert(payload).execute()
    if not res.data:
        raise HTTPException(400, "Não foi possível cadastrar a empresa.")
    return res.data[0]


@router.put("/tenants/{tenant_id}")
def update_tenant(tenant_id: str, dados: TenantUpdateIn, admin=Depends(require_admin)):
    update_data = {k: v for k, v in dados.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(400, "Nenhum dado informado para atualização.")

    res = supabase.table("tenants").update(update_data).eq("id", tenant_id).execute()
    if not res.data:
        raise HTTPException(404, "Empresa não encontrada.")
    return res.data[0]


@router.delete("/tenants/{tenant_id}")
def delete_tenant(tenant_id: str, admin=Depends(require_admin)):
    # Desativação segura (soft delete)
    res = supabase.table("tenants").update({"ativo": False}).eq("id", tenant_id).execute()
    if not res.data:
        raise HTTPException(404, "Empresa não encontrada.")
    return {"sucesso": True, "mensagem": "Empresa desativada com sucesso."}


# ─────────────────────────────────────────────────
# Rotas: Hub de Conectores & Teste em Tempo Real
# ─────────────────────────────────────────────────

@router.get("/tenants/{tenant_id}/connectors")
def get_tenant_connectors(tenant_id: str, admin=Depends(require_admin)):
    res = supabase.table("tenants").select("id, nome, nome_fantasia, conectores").eq("id", tenant_id).single().execute()
    if not res.data:
        raise HTTPException(404, "Empresa não encontrada.")
    return {
        "tenant_id": res.data["id"],
        "nome": res.data.get("nome_fantasia") or res.data.get("nome"),
        "conectores": res.data.get("conectores") or {}
    }


@router.post("/tenants/{tenant_id}/connectors")
def save_tenant_connectors(tenant_id: str, dados: ConnectorsSaveIn, admin=Depends(require_admin)):
    res = supabase.table("tenants").update({"conectores": dados.conectores}).eq("id", tenant_id).execute()
    if not res.data:
        raise HTTPException(404, "Empresa não encontrada.")
    return {"sucesso": True, "mensagem": "Conectores atualizados com sucesso!", "conectores": dados.conectores}


@router.post("/connectors/test")
def test_connector(dados: ConnectorTestIn, admin=Depends(require_admin)):
    tipo = dados.tipo
    cfg = dados.config or {}
    t0 = time.time()

    # 1. Teste TOTVS Moda (Bhan / API Rest)
    if tipo == "totvs_moda":
        base_url = (cfg.get("base_url") or "").rstrip("/")
        client_id = cfg.get("client_id")
        client_secret = cfg.get("client_secret")
        username = cfg.get("username")
        password = cfg.get("password")

        if not all([base_url, client_id, client_secret, username, password]):
            return {
                "sucesso": False,
                "mensagem": "Campos obrigatórios incompletos (Base URL, Client ID, Client Secret, Usuário e Senha)."
            }

        try:
            resp = httpx.post(
                f"{base_url}/authorization/v2/token",
                data={
                    "grant_type": "password",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "username": username,
                    "password": password,
                },
                verify=False,
                timeout=12.0,
            )
            latencia = int((time.time() - t0) * 1000)
            if resp.status_code == 200 and resp.json().get("access_token"):
                return {
                    "sucesso": True,
                    "mensagem": f"Conexão com TOTVS Moda validada com sucesso! Token gerado em {latencia}ms.",
                    "latencia_ms": latencia,
                    "status_code": 200,
                }
            return {
                "sucesso": False,
                "mensagem": f"Falha na autenticação TOTVS ({resp.status_code}): {resp.text[:250]}",
                "latencia_ms": latencia,
                "status_code": resp.status_code,
            }
        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Erro de conexão com o servidor TOTVS: {str(e)}",
                "latencia_ms": int((time.time() - t0) * 1000),
            }

    # 2. Teste Sankhya ERP (Gateway ou MobileLoginSP)
    if tipo == "sankhya":
        base_url = (cfg.get("base_url") or "").rstrip("/")
        app_key = cfg.get("app_key")
        client_token = cfg.get("client_token")
        username = cfg.get("username")
        password = cfg.get("password")

        if not base_url:
            return {"sucesso": False, "mensagem": "Endpoint Base URL do Sankhya é obrigatório."}

        try:
            # Tenta autenticação via Gateway REST ou MobileLogin
            headers = {"Content-Type": "application/json"}
            if app_key:
                headers["appkey"] = app_key
            if client_token:
                headers["token"] = client_token

            payload = {
                "serviceName": "MobileLoginSP.login",
                "requestBody": {
                    "NOMUSU": {"$": username or ""},
                    "INTERNO": {"$": password or ""},
                    "KEEPCONNECTED": {"$": "S"}
                }
            }
            resp = httpx.post(
                f"{base_url}/service.sbr?serviceName=MobileLoginSP.login&outputType=json",
                json=payload,
                headers=headers,
                timeout=12.0,
            )
            latencia = int((time.time() - t0) * 1000)
            if resp.status_code == 200:
                res_j = resp.json()
                if res_j.get("status") == "1" or res_j.get("responseBody", {}).get("jsessionid"):
                    return {
                        "sucesso": True,
                        "mensagem": f"Conexão com Sankhya ERP autenticada com sucesso ({latencia}ms).",
                        "latencia_ms": latencia,
                        "status_code": 200,
                    }
                msg_erro = res_j.get("statusMessage") or str(res_j)
                return {
                    "sucesso": False,
                    "mensagem": f"Sankhya respondeu com erro de login: {msg_erro[:250]}",
                    "latencia_ms": latencia,
                }
            return {
                "sucesso": False,
                "mensagem": f"Endpoint Sankhya retornou HTTP {resp.status_code}.",
                "latencia_ms": latencia,
            }
        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Não foi possível conectar ao Sankhya: {str(e)}",
                "latencia_ms": int((time.time() - t0) * 1000),
            }

    # 3. Teste Omie ERP
    if tipo == "omie":
        app_key = cfg.get("app_key") or cfg.get("client_id")
        app_secret = cfg.get("app_secret") or cfg.get("client_secret")
        if not app_key or not app_secret:
            return {"sucesso": False, "mensagem": "App Key e App Secret da Omie são obrigatórios."}
        try:
            resp = httpx.post(
                "https://app.omie.com.br/api/v1/geral/clientes/",
                json={
                    "call": "ListarClientes",
                    "app_key": app_key,
                    "app_secret": app_secret,
                    "param": [{"pagina": 1, "registros_por_pagina": 1, "apenas_importado_api": "N"}]
                },
                timeout=12.0
            )
            latencia = int((time.time() - t0) * 1000)
            if resp.status_code == 200:
                return {
                    "sucesso": True,
                    "mensagem": f"Conexão com Omie ERP autenticada com sucesso! Resposta em {latencia}ms.",
                    "latencia_ms": latencia,
                    "status_code": 200
                }
            return {
                "sucesso": False,
                "mensagem": f"Omie respondeu ({resp.status_code}): {resp.text[:250]}",
                "latencia_ms": latencia
            }
        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro de conexão com a Omie: {e}", "latencia_ms": int((time.time() - t0) * 1000)}

    # 4. Teste Bling ERP (API v3)
    if tipo == "bling":
        api_token = cfg.get("api_token") or cfg.get("token") or cfg.get("client_secret")
        if not api_token:
            return {"sucesso": False, "mensagem": "API Key / Token de acesso do Bling é obrigatório."}
        try:
            resp = httpx.get(
                "https://api.bling.com.br/v3/contatos?limite=1",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=12.0
            )
            latencia = int((time.time() - t0) * 1000)
            if resp.status_code in (200, 201):
                return {"sucesso": True, "mensagem": f"Conexão com Bling ERP autenticada com sucesso ({latencia}ms)!", "latencia_ms": latencia}
            return {"sucesso": False, "mensagem": f"Bling respondeu ({resp.status_code}): {resp.text[:200]}", "latencia_ms": latencia}
        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro ao conectar com Bling: {e}"}

    # 5. Teste Tiny ERP
    if tipo == "tiny":
        token = cfg.get("token") or cfg.get("api_token")
        if not token:
            return {"sucesso": False, "mensagem": "Token API do Tiny é obrigatório."}
        try:
            resp = httpx.post(
                "https://api.tiny.com.br/api2/info.php",
                data={"token": token, "formato": "json"},
                timeout=12.0
            )
            latencia = int((time.time() - t0) * 1000)
            if resp.status_code == 200 and resp.json().get("retorno", {}).get("status") != "Erro":
                return {"sucesso": True, "mensagem": f"Conexão com Tiny ERP validada com sucesso ({latencia}ms)!", "latencia_ms": latencia}
            return {"sucesso": False, "mensagem": f"Tiny retornou erro: {resp.text[:200]}", "latencia_ms": latencia}
        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro ao conectar com Tiny: {e}"}

    # 6. Teste Conta Azul
    if tipo == "conta_azul":
        token = cfg.get("token") or cfg.get("client_secret")
        if not token:
            return {"sucesso": False, "mensagem": "Token / Access Token do Conta Azul não informado."}
        try:
            resp = httpx.get(
                "https://api.contaazul.com/v1/customers?page=1&size=1",
                headers={"Authorization": f"Bearer {token}"},
                timeout=12.0
            )
            latencia = int((time.time() - t0) * 1000)
            if resp.status_code == 200:
                return {"sucesso": True, "mensagem": f"Conta Azul conectado com sucesso ({latencia}ms)!", "latencia_ms": latencia}
            return {"sucesso": False, "mensagem": f"Conta Azul respondeu ({resp.status_code}): {resp.text[:200]}", "latencia_ms": latencia}
        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro ao conectar ao Conta Azul: {e}"}

    # 7. Teste Senior Sistemas / SAP / Generic REST
    if tipo in ("senior", "sap_b1", "sap_s4hana", "oracle_netsuite", "oracle_cloud", "generic_rest", "totvs_protheus", "cigam", "wk_radar", "linx", "millenium"):
        base_url = (cfg.get("base_url") or "").rstrip("/")
        if not base_url:
            return {"sucesso": False, "mensagem": f"Base URL / Endpoint do conector '{tipo}' não informado."}
        try:
            headers = {}
            if cfg.get("token") or cfg.get("client_secret"):
                headers["Authorization"] = f"Bearer {cfg.get('token') or cfg.get('client_secret')}"
            resp = httpx.get(base_url, headers=headers, verify=False, timeout=10.0)
            latencia = int((time.time() - t0) * 1000)
            if resp.status_code in (200, 201, 204, 301, 302, 401, 403):
                return {
                    "sucesso": True,
                    "mensagem": f"Endpoint do sistema alcançado com sucesso ({latencia}ms, HTTP {resp.status_code}). Servidor online!",
                    "latencia_ms": latencia,
                    "status_code": resp.status_code
                }
            return {"sucesso": False, "mensagem": f"Endpoint retornou status HTTP {resp.status_code}.", "latencia_ms": latencia}
        except Exception as e:
            return {"sucesso": False, "mensagem": f"Não foi possível conectar ao endpoint: {e}"}

    # 8. Teste Banco de Dados SQL
    if tipo in ("database", "postgresql", "mysql", "sqlserver", "oracle_db"):
        host = cfg.get("host")
        port = int(cfg.get("port") or 5432)
        if not host:
            return {"sucesso": False, "mensagem": "Host do banco de dados não informado."}
        import socket
        try:
            s = socket.create_connection((host, port), timeout=6)
            s.close()
            latencia = int((time.time() - t0) * 1000)
            return {
                "sucesso": True,
                "mensagem": f"Porta {port} do servidor {host} acessível com sucesso ({latencia}ms)!",
                "latencia_ms": latencia,
            }
        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Não foi possível alcançar o host {host}:{port}: {e}",
                "latencia_ms": int((time.time() - t0) * 1000),
            }

    return {"sucesso": False, "mensagem": f"Tipo de conector '{tipo}' não suportado para teste automático."}


# ─────────────────────────────────────────────────
# Rotas: Gestão de Usuários & Senhas
# ─────────────────────────────────────────────────

def _gerar_senha_segura():
    """Gera uma senha provisória amigável, forte e fácil de digitar: Conexo@2026! + 3 dígitos"""
    chars = string.digits
    sufixo = "".join(secrets.choice(chars) for _ in range(4))
    return f"Conexo@{sufixo}!"


@router.get("/users")
def list_users(tenant_id: Optional[str] = None, admin=Depends(require_admin)):
    query = (
        supabase.table("conexo_usuarios")
        .select("id, auth_user_id, tenant_id, email, nome, setor, perfil, representante_codigo, ativo, created_at, ultimo_login")
        .order("created_at", desc=True)
    )
    if tenant_id:
        query = query.eq("tenant_id", tenant_id)
    
    users = query.execute().data or []

    # Busca nomes dos tenants
    tenants = {t["id"]: (t.get("nome_fantasia") or t.get("nome")) for t in supabase.table("tenants").select("id, nome, nome_fantasia").execute().data or []}

    for u in users:
        u["tenant_nome"] = tenants.get(u.get("tenant_id"), "Empresa desconhecida")

    return users


@router.post("/users")
def create_user(dados: UserCreateIn, admin=Depends(require_admin)):
    email = dados.email.strip().lower()
    senha = (dados.senha or "").strip() or _gerar_senha_segura()

    # 1. Cria usuário no Supabase Auth com senha e confirmação automática
    auth_user_id = None
    try:
        user_res = supabase.auth.admin.create_user({
            "email": email,
            "password": senha,
            "email_confirm": True,
        })
        auth_user_id = user_res.user.id
    except Exception as e:
        # Se usuário já existe no auth, tenta buscar id
        err_msg = str(e)
        if "already been registered" in err_msg or "already exists" in err_msg:
            try:
                listed = supabase.auth.admin.list_users()
                for au in getattr(listed, "users", []):
                    if au.email.lower() == email:
                        auth_user_id = au.id
                        # Atualiza a senha dele
                        supabase.auth.admin.update_user_by_id(auth_user_id, {"password": senha})
                        break
            except Exception:
                pass
        if not auth_user_id:
            raise HTTPException(400, f"Erro ao criar credencial no sistema de autenticação: {e}")

    # 2. Cria registro na tabela conexo_usuarios
    payload_user = {
        "auth_user_id": auth_user_id,
        "tenant_id": dados.tenant_id,
        "email": email,
        "nome": (dados.nome or email.split("@")[0]).strip(),
        "perfil": dados.perfil or "gestor",
        "setor": dados.setor or "Comercial",
        "representante_codigo": dados.representante_codigo,
        "ativo": True,
    }

    try:
        res_db = supabase.table("conexo_usuarios").insert(payload_user).execute()
        return {
            "sucesso": True,
            "usuario": res_db.data[0] if res_db.data else payload_user,
            "senha_provisoria": senha,
            "mensagem": f"Usuário {email} cadastrado com sucesso! Envie a senha provisória ao usuário."
        }
    except Exception as e:
        raise HTTPException(400, f"Erro ao salvar dados do usuário no banco: {e}")


@router.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: str, dados: ResetPasswordIn, admin=Depends(require_admin)):
    # 1. Busca usuário
    res = supabase.table("conexo_usuarios").select("*").eq("id", user_id).single().execute()
    u = res.data
    if not u:
        raise HTTPException(404, "Usuário não encontrado.")

    auth_id = u.get("auth_user_id")
    if not auth_id:
        raise HTTPException(400, "Usuário não possui ID de autenticação vinculado.")

    nova_senha = (dados.nova_senha or "").strip() or _gerar_senha_segura()

    try:
        supabase.auth.admin.update_user_by_id(auth_id, {"password": nova_senha})
        return {
            "sucesso": True,
            "email": u["email"],
            "nova_senha": nova_senha,
            "mensagem": f"Senha de {u['email']} redefinida com sucesso!"
        }
    except Exception as e:
        raise HTTPException(500, f"Erro ao atualizar senha no autenticador: {e}")


@router.put("/users/{user_id}")
def update_user(user_id: str, dados: UserUpdateIn, admin=Depends(require_admin)):
    update_data = {k: v for k, v in dados.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(400, "Nenhum campo fornecido.")

    res = supabase.table("conexo_usuarios").update(update_data).eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(404, "Usuário não encontrado.")
    return res.data[0]


@router.delete("/users/{user_id}")
def delete_user(user_id: str, admin=Depends(require_admin)):
    res = supabase.table("conexo_usuarios").select("auth_user_id").eq("id", user_id).single().execute()
    if res.data and res.data.get("auth_user_id"):
        try:
            supabase.auth.admin.delete_user(res.data["auth_user_id"])
        except Exception:
            pass

    supabase.table("conexo_usuarios").delete().eq("id", user_id).execute()
    return {"sucesso": True, "mensagem": "Usuário excluído com sucesso."}


# ─────────────────────────────────────────────────
# Rotas: Logs de Erro & Auditoria
# ─────────────────────────────────────────────────

@router.get("/logs")
def get_logs(
    limit: int = 50,
    apenas_erros: bool = False,
    usuario: Optional[str] = None,
    admin=Depends(require_admin)
):
    query = supabase.table("conexo_logs").select("*").order("created_at", desc=True).limit(limit)
    if apenas_erros:
        query = query.eq("sucesso", False)
    if usuario:
        query = query.ilike("usuario", f"%{usuario}%")

    logs = query.execute().data or []
    return logs


# ─────────────────────────────────────────────────
# Rotas: Gestão Financeira SaaS (Conexo.dev)
# ─────────────────────────────────────────────────

@router.get("/financeiro")
def get_financeiro(admin=Depends(require_admin)):
    tenants = supabase.table("tenants").select("*").execute().data or []

    # Contagem de perguntas do mês por tenant
    hoje = datetime.date.today()
    inicio_mes = hoje.replace(day=1).isoformat()

    clientes_financeiro = []
    mrr_total = 0

    for t in tenants:
        tid = t["id"]
        v_mensal = float(t.get("valor_mensal") or 0)
        if t.get("ativo"):
            mrr_total += v_mensal

        # Busca consultas daquele tenant
        try:
            r = supabase.rpc("conexo_executar_leitura", {
                "query_str": f"""
                SELECT COUNT(*) as qtd
                FROM conexo_logs l
                INNER JOIN conexo_usuarios u ON u.email = l.usuario
                WHERE u.tenant_id = '{tid}' AND l.created_at >= '{inicio_mes}'
                """
            }).execute()
            perguntas_cli = int(r.data[0].get("qtd") or 0) if r.data else 0
        except Exception:
            perguntas_cli = 0

        custo_ia = round(perguntas_cli * 0.021, 2)
        margem = round(v_mensal - custo_ia, 2)

        clientes_financeiro.append({
            "tenant_id": tid,
            "nome": t.get("nome_fantasia") or t.get("nome"),
            "cnpj": t.get("cnpj"),
            "plano": t.get("plano") or "Enterprise",
            "valor_mensal": v_mensal,
            "dia_vencimento": t.get("dia_vencimento") or 10,
            "status_pagamento": t.get("status_pagamento") or "em_dia",
            "ativo": t.get("ativo", True),
            "perguntas_mes": perguntas_cli,
            "custo_ia_mes": custo_ia,
            "margem_liquida": margem,
        })

    return {
        "mrr_total": mrr_total,
        "arr_anual": round(mrr_total * 12, 2),
        "total_clientes": len(clientes_financeiro),
        "clientes": clientes_financeiro,
    }
