import os
import requests
import datetime
import urllib3

# Desativa avisos de SSL para chamadas internas do TOTVS Bhan
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TotvsClient:
    BASE_URL = os.environ.get("TOTVS_BASE_URL", "https://www30.bhan.com.br:9443/api/totvsmoda")
    CLIENT_ID = os.environ.get("TOTVS_CLIENT_ID", "designtexapiv2")
    CLIENT_SECRET = os.environ.get("TOTVS_CLIENT_SECRET", "5871699427")
    USERNAME = os.environ.get("TOTVS_USERNAME", "samuel")
    PASSWORD = os.environ.get("TOTVS_PASSWORD", "2025")

    _token = None
    _token_expires_at = 0

    @classmethod
    def get_token(cls) -> str:
        now = datetime.datetime.now().timestamp()
        if cls._token and now < cls._token_expires_at:
            return cls._token

        data = {
            "grant_type": "password",
            "client_id": cls.CLIENT_ID,
            "client_secret": cls.CLIENT_SECRET,
            "username": cls.USERNAME,
            "password": cls.PASSWORD,
        }

        resp = requests.post(
            f"{cls.BASE_URL}/authorization/v2/token",
            data=data,
            verify=False,
            timeout=15,
        )
        if not resp.ok:
            raise RuntimeError(f"Erro autenticando no TOTVS Moda: {resp.status_code} - {resp.text}")

        res_json = resp.json()
        cls._token = res_json.get("access_token")
        expires_in = res_json.get("expires_in", 3600)
        cls._token_expires_at = now + expires_in - 300
        return cls._token

    @classmethod
    def get_headers(cls) -> dict:
        token = cls.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @classmethod
    def consultar_estatisticas(cls, customer_code: str, branch_code: str = "001") -> dict:
        """
        Consulta estatísticas financeiras e de crédito ao vivo do cliente no TOTVS.
        Retorna atrasos, faturas em aberto, limite total e compras históricas.
        """
        headers = cls.get_headers()
        url = f"{cls.BASE_URL}/person/v2/person-statistics?branchCode={branch_code}&customerCode={customer_code}"
        resp = requests.get(url, headers=headers, verify=False, timeout=15)
        if not resp.ok:
            raise RuntimeError(f"Erro ao buscar estatísticas do cliente {customer_code} no TOTVS: {resp.status_code}")
        return resp.json()

    @classmethod
    def consultar_boletos(cls, customer_code: str, branch_code: str = "1", status: str = "0") -> list:
        """
        Busca títulos/boletos do cliente no TOTVS (Contas a Receber).
        status '0' = apenas em aberto.
        """
        headers = cls.get_headers()
        payload = {
            "filter": {
                "branchCodeList": [int(branch_code)],
                "customerCodeList": [int(customer_code)],
                "dischargeTypeList": [0] if status == "0" else [],
            },
            "pageSize": 100,
            "page": 1,
        }
        url = f"{cls.BASE_URL}/accounts-receivable/v2/documents/search"
        resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=15)
        if not resp.ok:
            return []
        
        items = resp.json().get("items", []) or []
        # Filtra títulos válidos em aberto
        validos = []
        for i in items:
            if i.get("status") is not None and int(i.get("status")) not in (1,):
                continue
            if i.get("paymentDate") or i.get("settlementDate"):
                continue
            validos.append(i)
        return validos
