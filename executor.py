from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# intents que NÃO chamam banco (tratadas no fluxo)
NAO_DB = {"fora_de_escopo", "pedir_esclarecimento"}

# intents que existem como RPC no Supabase
RPCS = {
    "conexo_vendas_periodo",
    "conexo_comparativo_mes",
    "conexo_comparativo_ano",
    "conexo_ranking_vendedores",
    "conexo_vendedores_abaixo_meta",
    "conexo_top_produtos",
    "conexo_top_clientes",
    "conexo_clientes_inativos",
    "conexo_vendas_regiao",
    "conexo_top_cores",
    "conexo_relatorio_periodo",
}

# RPCs que suportam filtro por representante (vendedor vê só o dele)
RPCS_COM_REP = {
    "conexo_ranking_vendedores",
    "conexo_vendas_periodo",
    "conexo_top_clientes",
    "conexo_top_produtos",
    "conexo_vendas_regiao",
    "conexo_top_cores",
}


import unicodedata

def desacentuar(txt: str) -> str:
    if not txt:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(txt)) if unicodedata.category(c) != "Mn"
    ).lower().strip()


def executar(intent: str, params: dict, ctx: dict | None = None):
    """
    Executa a intent. ctx contém tenant_id e rep do token (multi-tenant).
    """
    # Inteligência de mercado tem caminho próprio
    if intent == "conexo_inteligencia_mercado":
        from mercado.motor import analisar_mercado
        return analisar_mercado(params, ctx or {})

    # Consulta Financeira e de Crédito ao vivo no ERP TOTVS Moda
    if intent == "conexo_consulta_financeiro_cliente":
        termo = (params.get("cliente") or "").strip()
        if not termo:
            raise ValueError("Nome ou código do cliente não fornecido.")

        termo_limpo = desacentuar(termo)
        termo_sem_espaco = termo_limpo.replace(" ", "")

        if termo.isdigit():
            sql_cli = f"SELECT id, codigo, razao_social, nome_fantasia, limite_credito, saldo_disponivel, saldo_atraso FROM clientes WHERE codigo = '{termo}' LIMIT 1"
        else:
            sql_cli = f"""
            SELECT id, codigo, razao_social, nome_fantasia, limite_credito, saldo_disponivel, saldo_atraso 
            FROM clientes 
            WHERE REPLACE(LOWER(razao_social), ' ', '') LIKE '%{termo_sem_espaco}%'
               OR razao_social ILIKE '%{termo}%'
               OR REPLACE(LOWER(nome_fantasia), ' ', '') LIKE '%{termo_sem_espaco}%'
               OR nome_fantasia ILIKE '%{termo}%'
               OR codigo ILIKE '%{termo}%'
            LIMIT 1
            """
        resp_cli = supabase.rpc("conexo_executar_leitura", {"query_str": sql_cli.strip().rstrip(";")}).execute()
        cli_rows = resp_cli.data or []
        if not cli_rows:
            return [{"mensagem": f"Cliente '{termo}' não localizado no cadastro da Designtex."}]

        cli = cli_rows[0]
        cod_cliente = str(cli.get("codigo") or "").strip()
        razao_social = cli.get("razao_social") or termo

        from totvs_client import TotvsClient
        import datetime

        hoje = datetime.date.today().strftime("%Y-%m-%d")
        stats = {}
        boletos_raw = []
        try:
            stats = TotvsClient.consultar_estatisticas(cod_cliente)
            boletos_raw = TotvsClient.consultar_boletos(cod_cliente)
        except Exception as e:
            print(f"[TotvsClient] Erro ao consultar TOTVS para {cod_cliente}: {e}")

        qtd_atrasadas = int(stats.get("quantityInstallmentsDelayed") or 0)
        valor_atrasado = float(stats.get("totalInstallmentsDelayed") or 0)
        atraso_medio = int(stats.get("averageDelay") or 0)
        maior_atraso = int(stats.get("maximumDelay") or 0)

        qtd_abertas = int(stats.get("quantityInstallmentsOpen") or 0)
        saldo_utilizado = float(stats.get("totalInstallmentsOpen") or 0)
        limite_credito = float(cli.get("limite_credito") or 0)
        saldo_disponivel = limite_credito - saldo_utilizado

        titulos_atrasados = []
        for b in boletos_raw:
            venc = (b.get("expiredDate") or "")[:10]
            val = float(b.get("installmentValue") or 0)
            if venc and venc < hoje:
                try:
                    d_venc = datetime.date.fromisoformat(venc)
                    d_hoje = datetime.date.fromisoformat(hoje)
                    dias = (d_hoje - d_venc).days
                except Exception:
                    dias = 0
                titulos_atrasados.append({
                    "vencimento": datetime.date.fromisoformat(venc).strftime("%d/%m/%Y") if "-" in venc else venc,
                    "valor": val,
                    "dias_atraso": dias,
                    "documento": b.get("documentCode") or b.get("number") or "Duplicata",
                    "parcela": b.get("installmentNumber") or 1,
                })

        # Sincroniza a tabela clientes no Supabase em segundo plano
        try:
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            supabase.table("clientes").update({
                "saldo_atraso": valor_atrasado,
                "saldo_disponivel": saldo_disponivel,
                "sincronizado_totvs_em": now_iso,
                "updated_at": now_iso,
            }).eq("codigo", cod_cliente).execute()
        except Exception as sync_err:
            print(f"[Sync] Erro ao atualizar clientes no Supabase: {sync_err}")

        linhas_resumo = [
            {
                "indicador": "Faturas em Atraso",
                "quantidade": f"{qtd_atrasadas} fatura(s)",
                "valor_total": valor_atrasado,
                "status": "EM ATRASO / INADIMPLENTE" if qtd_atrasadas > 0 else "EM DIA",
                "detalhe": f"Atraso médio: {atraso_medio} dias | Maior atraso: {maior_atraso} dias" if qtd_atrasadas > 0 else "Nenhum atraso registrado",
                "razao_social": razao_social,
                "codigo": cod_cliente,
            },
            {
                "indicador": "Faturas em Aberto (Total Utilizado)",
                "quantidade": f"{qtd_abertas} fatura(s)",
                "valor_total": saldo_utilizado,
                "status": "Total a Vencer + Vencido",
                "detalhe": "Soma de todos os títulos ativos no TOTVS",
                "razao_social": razao_social,
                "codigo": cod_cliente,
            },
            {
                "indicador": "Limite de Crédito Aprovado",
                "quantidade": "-",
                "valor_total": limite_credito,
                "status": "Definido no TOTVS",
                "detalhe": "Limite concedido para faturamento a prazo",
                "razao_social": razao_social,
                "codigo": cod_cliente,
            },
            {
                "indicador": "Saldo Disponível para Novos Pedidos",
                "quantidade": "-",
                "valor_total": saldo_disponivel,
                "status": "ESTOURADO" if saldo_disponivel < 0 else "LIBERADO",
                "detalhe": f"Margem de crédito ({round((saldo_utilizado / limite_credito * 100), 1) if limite_credito > 0 else 100}% consumido)",
                "razao_social": razao_social,
                "codigo": cod_cliente,
            },
        ]

        if titulos_atrasados:
            for idx, t in enumerate(titulos_atrasados, 1):
                linhas_resumo.append({
                    "indicador": f"Boleto Vencido #{idx}",
                    "quantidade": f"{t['dias_atraso']} dias de atraso",
                    "valor_total": t["valor"],
                    "status": f"Venceu em {t['vencimento']}",
                    "detalhe": f"Doc {t['documento']} (Parc {t['parcela']})",
                    "razao_social": razao_social,
                    "codigo": cod_cliente,
                })

        return linhas_resumo

    # Consulta de Estoque de Pronto-Entrega
    if intent == "conexo_consulta_estoque":
        produto = params.get("produto", "").strip()
        cor = params.get("cor", "").strip()
        
        where_clauses = []
        if produto:
            terms = [desacentuar(t) for t in produto.split() if len(t) >= 2]
            for term in terms:
                where_clauses.append(
                    f"(translate(lower(e.descricao), 'áàâãéèêíïóôõöúçñ', 'aaaeeeiooooucn') LIKE '%{term}%' OR lower(e.cod_produto) LIKE '%{term}%')"
                )
        if cor:
            terms = [desacentuar(t) for t in cor.split() if len(t) >= 1]
            for term in terms:
                where_clauses.append(
                    f"(translate(lower(e.cor), 'áàâãéèêíïóôõöúçñ', 'aaaeeeiooooucn') LIKE '%{term}%' OR translate(lower(e.descricao), 'áàâãéèêíïóôõöúçñ', 'aaaeeeiooooucn') LIKE '%{term}%' OR lower(e.cor_codigo) LIKE '%{term}%')"
                )
                
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        sql = f"""
        WITH reservas_vivas AS (
            SELECT 
                item->>'colorCode' as cor_codigo,
                COALESCE(SUM((item->>'quantity')::numeric), 0) as reserva_pedidos
            FROM pedidos_totvs p,
            LATERAL jsonb_array_elements(
                CASE WHEN jsonb_typeof(p.items_json) = 'array' THEN p.items_json ELSE '[]'::jsonb END
            ) item
            WHERE p.status IN ('InProgress', 'Blocked', 'InComposition')
            GROUP BY item->>'colorCode'
        )
        SELECT 
            e.cod_produto, 
            e.descricao, 
            e.cor, 
            e.cor_codigo, 
            GREATEST(0, ROUND((COALESCE(NULLIF(e.estoque_1, 0), e.quantidade_disponivel + e.quantidade_reservada, 0) - GREATEST(COALESCE(r.reserva_pedidos, 0), e.quantidade_reservada))::numeric, 1)) AS quantidade_disponivel, 
            GREATEST(COALESCE(r.reserva_pedidos, 0), e.quantidade_reservada) AS quantidade_reservada, 
            ROUND(GREATEST(COALESCE(e.estoque_1, 0), e.quantidade_disponivel + e.quantidade_reservada)::numeric, 1) AS estoque_fisico, 
            e.categoria, 
            e.unidade, 
            e.hex_color 
        FROM estoque_pe e
        LEFT JOIN reservas_vivas r ON e.cor_codigo = r.cor_codigo
        WHERE {where_sql} 
        ORDER BY quantidade_disponivel DESC LIMIT 30
        """
        
        resp = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        return resp.data

    # Consulta de Programação PCP (Produção de Tecidos)
    if intent == "conexo_consulta_programacao":
        produto = params.get("produto", "").strip()
        cor = params.get("cor", "").strip()
        
        where_clauses = []
        if produto:
            terms = [desacentuar(t) for t in produto.split() if len(t) >= 2]
            for term in terms:
                where_clauses.append(
                    f"(translate(lower(nome_tecido), 'áàâãéèêíïóôõöúçñ', 'aaaeeeiooooucn') LIKE '%{term}%' OR lower(cod_tecido) LIKE '%{term}%' OR translate(lower(tipo), 'áàâãéèêíïóôõöúçñ', 'aaaeeeiooooucn') LIKE '%{term}%')"
                )
        if cor:
            terms = [desacentuar(t) for t in cor.split() if len(t) >= 1]
            for term in terms:
                where_clauses.append(
                    f"(translate(lower(nome_cor), 'áàâãéèêíïóôõöúçñ', 'aaaeeeiooooucn') LIKE '%{term}%' OR lower(cod_cor) LIKE '%{term}%')"
                )
                
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        sql = f"SELECT op, cod_tecido, nome_tecido, cod_cor, nome_cor, quantidade_solicitada, quantidade_disponivel, previsao_faturamento, tipo FROM programacoes WHERE {where_sql} ORDER BY quantidade_solicitada DESC LIMIT 30"
        
        resp = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        return resp.data

    # Consulta e Relatório Unificado de Pedidos (Portal de Vendas + ERP TOTVS)
    if intent == "conexo_consulta_pedidos":
        import datetime
        import re

        ARTICLE_SYNONYMS = {
            "1000": ["1000", "tricoline paris"],
            "1001": ["1001", "verano flame"],
            "1002": ["1002", "linho deluxe"],
            "1003": ["1003", "verano chambrey", "verano chambray"],
            "1004": ["1004", "fine flex jeans"],
            "1005": ["1005", "rush peletizado", "tecido rush"],
            "1006": ["1006", "sarja nature"],
            "1008": ["1008", "botone color"],
            "1010": ["1010", "tricoline havana"],
            "1011": ["1011", "tricoline deluxe"],
            "1013": ["1013", "royale fio tinto", "tecido royale"],
            "1015": ["1015", "tricoline premium"],
            "1016": ["1016", "veneto fio tinto"],
            "1017": ["1017", "sarja caribe flex", "caribe flex"],
            "1018": ["1018", "tessera rustic"],
            "1019": ["1019", "tricoline londres"],
            "1021": ["1021", "linho deluxe maquinetado"],
            "1024": ["1024", "sarja caribe light", "caribe light"],
            "1025": ["1025", "verano striped"],
            "1028": ["1028", "tricoline top line", "top line"],
            "1030": ["1030", "verano listrado elegance"],
            "1031": ["1031", "rayon balli"],
            "1032": ["1032", "chambray two tone"],
            "1033": ["1033", "sarja flex"],
            "1038": ["1038", "maqtton rustic"],
            "1042": ["1042", "popeline primore"],
            "1043": ["1043", "verano linho"],
            "1044": ["1044", "linho panama"],
            "1045": ["1045", "sarja zara"],
            "1046": ["1046", "verano arizona"],
            "1049": ["1049", "creta xadrez"],
            "1052": ["1052", "panama c/ elas", "panama com elastano"],
            "1053": ["1053", "linho ipanema"],
            "1055": ["1055", "verano milano"],
            "1057": ["1057", "arizona two toner"],
            "1058": ["1058", "striped two toner"],
            "1063": ["1063", "oxford linho"],
            "1064": ["1064", "botone color plus"],
            "1065": ["1065", "tricoline classic"],
            "1071": ["1071", "mega soft"],
            "1073": ["1073", "linho xadrez"],
            "1074": ["1074", "linho blend"],
            "1076": ["1076", "verano linho plus"],
            "1078": ["1078", "linho maquinetado"],
            "1082": ["1082", "viscose deluxe"],
            "1084": ["1084", "amalfi rustic"],
            "1087": ["1087", "mediterraneo"],
            "1088": ["1088", "riviera"],
            "1089": ["1089", "linho belga"],
            "1090": ["1090", "havana confort"],
            "1091": ["1091", "bari rustic"],
            "1093": ["1093", "verano striped alvejado"],
            "1095": ["1095", "linea rustic"],
            "1096": ["1096", "sierra maquinetado"],
            "1097": ["1097", "sarja byskay", "byskay flex"],
            "1098": ["1098", "maqtton linho"],
            "1099": ["1099", "verano flame 160"],
            "1100": ["1100", "porto fino"],
            "1101": ["1101", "sorrento"],
            "1103": ["1103", "cierro linho"],
            "1104": ["1104", "listrado medio"],
            "1105": ["1105", "sierra linho"],
            "1107": ["1107", "linho caraiva", "caraiva"],
            "1109": ["1109", "provance flame"],
            "1112": ["1112", "verano chambrey 160", "verano chambray 160"],
            "1113": ["1113", "chambray two tone 160"],
            "1114": ["1114", "sarja nature 170"],
            "1117": ["1117", "sarja dakota", "sarja prowork"],
            "1118": ["1118", "ilhabela rustic", "ilhabela"],
            "1119": ["1119", "linho maragogi", "linho maragoggi", "maragogi", "maragoggi"],
            "1120": ["1120", "capitolio rustic", "capitolio"],
            "1121": ["1121", "chambray paraty", "paraty"],
            "1122": ["1122", "sarja inhotim", "inhotim"],
            "1123": ["1123", "linho atalaia", "atalaia"],
            "1124": ["1124", "rush premium"],
            "1126": ["1126", "sarja velvet"],
            "1127": ["1127", "sarja prowork profissional"],
            "1129": ["1129", "sarja urban flex"],
            "1132": ["1132", "sarja street"],
        }

        artigo = (params.get("artigo") or "").strip()
        cor = (params.get("cor") or "").strip()
        status_filtro = (params.get("status_filtro") or "carteira").strip().lower()
        cliente = (params.get("cliente") or "").strip()
        representante = (params.get("representante") or "").strip()
        inicio = (params.get("inicio") or "2026-01-01").strip()
        fim = (params.get("fim") or datetime.date.today().strftime("%Y-%m-%d")).strip()

        # Se o usuário for representante logado, restringe ao código dele
        if ctx and ctx.get("rep"):
            representante = str(ctx["rep"]).strip()

        # Filtro de artigo (código + nomes sinônimos exatamente como no Portal)
        art_clean = desacentuar(artigo)
        code_match = re.search(r"\b(1\d{3})\b", art_clean)
        art_code = code_match.group(1) if code_match else None
        if not art_code and art_clean:
            for k, syns in ARTICLE_SYNONYMS.items():
                if any(s in art_clean for s in syns):
                    art_code = k
                    break

        if art_code:
            syns = ARTICLE_SYNONYMS.get(art_code, [art_code])
            name_terms = [s for s in syns if not s.isdigit()]
            name_cond_pi = " OR ".join(f"pi.descricao_item ILIKE '%{t}%'" for t in name_terms) or "FALSE"
            name_cond_pt = " OR ".join(
                f"COALESCE(item->>'name', '') ILIKE '%{t}%' OR COALESCE(item->>'referenceName', '') ILIKE '%{t}%'"
                for t in name_terms
            ) or "FALSE"
            art_where_pi = f"(TRIM(COALESCE(pi.cod_produto, '')) = '{art_code}' OR ({name_cond_pi}))"
            art_where_pt = f"(regexp_replace(COALESCE(item->>'referenceCode', ''), '[^0-9]', '', 'g') = '{art_code}' OR ({name_cond_pt}))"
            art_label = f"{art_code} - {name_terms[0].upper()}" if name_terms else art_code
            art_select_col = f"'{art_label}' AS artigo,"
        elif art_clean:
            safe_art = art_clean.replace("'", "''")
            art_where_pi = f"(pi.descricao_item ILIKE '%{safe_art}%' OR pi.cod_produto ILIKE '%{safe_art}%')"
            art_where_pt = f"(COALESCE(item->>'name', '') ILIKE '%{safe_art}%' OR COALESCE(item->>'referenceName', '') ILIKE '%{safe_art}%' OR COALESCE(item->>'referenceCode', '') ILIKE '%{safe_art}%')"
            art_select_col = f"'{safe_art.upper()}' AS artigo,"
        else:
            art_where_pi = "1=1"
            art_where_pt = "1=1"
            art_select_col = ""

        # Filtro de cor
        if cor:
            safe_cor = cor.replace("'", "''")
            cor_where_pi = f"COALESCE(pi.cor_item, '') ILIKE '%{safe_cor}%'"
            cor_where_pt = f"(COALESCE(item->>'colorName', '') ILIKE '%{safe_cor}%' OR COALESCE(item->>'colorCode', '') ILIKE '%{safe_cor}%')"
        else:
            cor_where_pi = "1=1"
            cor_where_pt = "1=1"

        # Filtro de status
        if status_filtro in ("bloqueado", "bloqueados"):
            status_where = "status_norm = 'Bloqueado'"
        elif status_filtro in ("em_andamento", "andamento"):
            status_where = "status_norm = 'Em andamento'"
        elif status_filtro in ("faturado", "faturados", "atendido", "atendidos"):
            status_where = "status_norm IN ('Atendido', 'Parcialmente Atendido')"
        elif status_filtro == "todos":
            status_where = "status_norm <> 'Cancelado'"
        else:
            # 'carteira': exatamente o filtro padrão do Portal (Em andamento, Bloqueado, Em composição, Em análise)
            status_where = "status_norm IN ('Em andamento', 'Bloqueado', 'Em composição', 'Em análise')"

        extra_order_filters = [status_where]
        if inicio:
            extra_order_filters.append(f"data_pedido >= '{inicio}'::date")
        if fim:
            extra_order_filters.append(f"data_pedido <= '{fim}'::date")
        if cliente:
            safe_cli = cliente.replace("'", "''")
            extra_order_filters.append(f"cliente ILIKE '%{safe_cli}%'")
        if representante:
            safe_rep = representante.replace("'", "''")
            extra_order_filters.append(f"(rep_codigo = '{safe_rep}' OR rep_nome ILIKE '%{safe_rep}%')")

        where_orders_sql = " AND ".join(extra_order_filters)

        sql = f"""
        WITH pedidos_unificados AS (
            SELECT
                p.id AS local_id,
                COALESCE(pt.totvs_order_code, p.numero) AS pedido,
                COALESCE(pt.representante_codigo, p.representante_codigo) AS rep_codigo,
                COALESCE(pt.representante_nome, r.nome, '') AS rep_nome,
                COALESCE(c.razao_social, c.nome_fantasia, pt.cliente_nome, p.payload_totvs->>'customerName', '-') AS cliente,
                COALESCE(p.tipo_pedido, '-') AS tipo,
                CASE
                    WHEN p.tipo_pedido = 'OP' OR p.numero_op IS NOT NULL THEN COALESCE(p.numero_op, p.payload_totvs->>'batchOrder', NULLIF(pt.lote_pedido, 'PE'), 'OP')
                    ELSE COALESCE(NULLIF(pt.lote_pedido, ''), p.payload_totvs->>'batchOrder', p.tipo_pedido, '-')
                END AS lote_pedido,
                CASE
                    WHEN COALESCE(pt.status, p.status) IN ('InProgress', 'Em andamento', 'open', 'aberto', '1') THEN 'Em andamento'
                    WHEN COALESCE(pt.status, p.status) IN ('Blocked', 'Bloqueado', '5') THEN 'Bloqueado'
                    WHEN COALESCE(pt.status, p.status) IN ('InComposition', 'Em composição', 'Em composicao', '7') THEN 'Em composição'
                    WHEN COALESCE(pt.status, p.status) IN ('Pending', 'InAnalysis', 'Em análise', 'Em analise', '8') THEN 'Em análise'
                    WHEN COALESCE(pt.status, p.status) IN ('PartiallyAnswered', 'Parcialmente Atendido', '3') THEN 'Parcialmente Atendido'
                    WHEN COALESCE(pt.status, p.status) IN ('Attended', 'Atendido', 'Faturado', '4') THEN 'Atendido'
                    WHEN COALESCE(pt.status, p.status) IN ('Canceled', 'Cancelled', 'Cancelado', '6', '9') THEN 'Cancelado'
                    ELSE COALESCE(pt.status, p.status)
                END AS status_norm,
                p.created_at::date AS data_pedido,
                COALESCE(pt.valor_total, p.valor_total, 0)::numeric AS order_valor_total,
                pt.items_json AS pt_items_json
            FROM pedidos p
            LEFT JOIN clientes c ON c.id = p.cliente_id
            LEFT JOIN representantes r ON r.codigo = p.representante_codigo
            LEFT JOIN LATERAL (
                SELECT pt2.*
                FROM pedidos_totvs pt2
                WHERE pt2.representante_codigo = p.representante_codigo
                  AND (
                      pt2.totvs_order_code = p.numero
                      OR (p.payload_totvs->>'orderId' IS NOT NULL AND pt2.totvs_order_id = p.payload_totvs->>'orderId')
                  )
                ORDER BY pt2.id DESC
                LIMIT 1
            ) pt ON true

            UNION ALL

            SELECT
                NULL::bigint AS local_id,
                pt.totvs_order_code AS pedido,
                pt.representante_codigo AS rep_codigo,
                COALESCE(pt.representante_nome, r.nome, '') AS rep_nome,
                COALESCE(pt.cliente_nome, '-') AS cliente,
                '-' AS tipo,
                COALESCE(NULLIF(pt.lote_pedido, ''), '-') AS lote_pedido,
                CASE
                    WHEN pt.status IN ('InProgress', 'Em andamento', 'open', 'aberto', '1') THEN 'Em andamento'
                    WHEN pt.status IN ('Blocked', 'Bloqueado', '5') THEN 'Bloqueado'
                    WHEN pt.status IN ('InComposition', 'Em composição', 'Em composicao', '7') THEN 'Em composição'
                    WHEN pt.status IN ('Pending', 'InAnalysis', 'Em análise', 'Em analise', '8') THEN 'Em análise'
                    WHEN pt.status IN ('PartiallyAnswered', 'Parcialmente Atendido', '3') THEN 'Parcialmente Atendido'
                    WHEN pt.status IN ('Attended', 'Atendido', 'Faturado', '4') THEN 'Atendido'
                    WHEN pt.status IN ('Canceled', 'Cancelled', 'Cancelado', '6', '9') THEN 'Cancelado'
                    ELSE pt.status
                END AS status_norm,
                pt.data_pedido::date AS data_pedido,
                COALESCE(pt.valor_total, 0)::numeric AS order_valor_total,
                pt.items_json AS pt_items_json
            FROM pedidos_totvs pt
            LEFT JOIN representantes r ON r.codigo = pt.representante_codigo
            WHERE NOT EXISTS (
                SELECT 1 FROM pedidos p
                WHERE p.representante_codigo = pt.representante_codigo
                  AND (
                      p.numero = pt.totvs_order_code
                      OR (p.payload_totvs->>'orderId' IS NOT NULL AND p.payload_totvs->>'orderId' = pt.totvs_order_id)
                  )
            )
        ),
        pedidos_filtrados AS (
            SELECT *
            FROM pedidos_unificados
            WHERE {where_orders_sql}
        ),
        itens_resolvidos AS (
            SELECT
                pf.rep_codigo,
                pf.pedido,
                pf.cliente,
                pf.tipo,
                pf.lote_pedido,
                pf.status_norm AS status,
                pf.data_pedido,
                COALESCE(pi.quantidade, 0)::numeric AS metros_item,
                CASE
                    WHEN COALESCE(pi.subtotal, 0) > 0 AND NOT (
                        (SELECT COUNT(*) FROM pedido_itens pi2 WHERE pi2.pedido_id = pf.local_id) > 1
                        AND pf.order_valor_total > 0
                        AND COALESCE(pi.subtotal, 0) >= pf.order_valor_total
                    ) THEN pi.subtotal::numeric
                    ELSE ROUND((COALESCE(pi.quantidade, 0)::numeric * COALESCE(pi.preco_unitario, 0)::numeric), 2)
                END AS valor_item
            FROM pedidos_filtrados pf
            JOIN pedido_itens pi ON pi.pedido_id = pf.local_id
            WHERE {art_where_pi} AND {cor_where_pi}

            UNION ALL

            SELECT
                pf.rep_codigo,
                pf.pedido,
                pf.cliente,
                pf.tipo,
                pf.lote_pedido,
                pf.status_norm AS status,
                pf.data_pedido,
                COALESCE((item->>'quantity')::numeric, 0) AS metros_item,
                ROUND((COALESCE((item->>'quantity')::numeric, 0) * COALESCE((item->>'price')::numeric, 0)), 2) AS valor_item
            FROM pedidos_filtrados pf
            CROSS JOIN LATERAL jsonb_array_elements(
                CASE WHEN jsonb_typeof(pf.pt_items_json) = 'array' THEN pf.pt_items_json ELSE '[]'::jsonb END
            ) AS item
            WHERE (pf.local_id IS NULL OR NOT EXISTS (SELECT 1 FROM pedido_itens pi3 WHERE pi3.pedido_id = pf.local_id))
              AND {art_where_pt} AND {cor_where_pt}
        )
        SELECT
            rep_codigo AS rep,
            pedido,
            cliente,
            {art_select_col}
            tipo,
            lote_pedido,
            status,
            data_pedido,
            ROUND(SUM(metros_item), 2) AS metros,
            ROUND(SUM(valor_item), 2) AS valor_total,
            COUNT(*) OVER() AS total_pedidos_geral
        FROM itens_resolvidos
        GROUP BY rep_codigo, pedido, cliente, tipo, lote_pedido, status, data_pedido
        HAVING SUM(metros_item) > 0 OR SUM(valor_item) > 0
        ORDER BY
            CASE WHEN pedido LIKE 'W%' THEN 0 ELSE 1 END,
            CASE WHEN pedido LIKE 'W%' THEN data_pedido END DESC,
            NULLIF(regexp_replace(pedido, '[^0-9]', '', 'g'), '')::bigint DESC NULLS LAST
        """

        resp = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        return resp.data

    # Consulta geral dinâmica (Text-to-SQL)
    if intent == "conexo_consulta_geral":
        perfil_usuario = (ctx.get("perfil") or "gestor").lower() if ctx else "gestor"
        if perfil_usuario not in ("gestor", "admin", "diretoria", "supervisor"):
            raise ValueError("Apenas gestores e administradores podem realizar consultas personalizadas no banco de dados.")
        sql = params.get("sql", "")
        if sql:
            import re
            sql = sql.strip().rstrip(";")
            # Corrige automaticamente item->>'totalValue' (campo inexistente no JSON) para quantity * price
            sql = re.sub(
                r"\(\s*item->>'totalValue'\s*\)::numeric",
                "(COALESCE((item->>'settledQuantity')::numeric, (item->>'quantity')::numeric, 0) * COALESCE((item->>'price')::numeric, 0))",
                sql,
                flags=re.IGNORECASE,
            )
            sql = re.sub(
                r"item->>'totalValue'",
                "((COALESCE((item->>'settledQuantity')::numeric, (item->>'quantity')::numeric, 0) * COALESCE((item->>'price')::numeric, 0))::text)",
                sql,
                flags=re.IGNORECASE,
            )
            # Se a query cruza estoque_pe com item->>'referenceCode' sem regexp_replace, sanitiza para extrair apenas dígitos
            if "estoque_pe" in sql.lower() and "referencecode" in sql.lower() and "regexp_replace" not in sql.lower():
                sql = re.sub(
                    r"item->>'referenceCode'",
                    "regexp_replace(COALESCE(item->>'referenceCode', ''), '[^0-9]', '', 'g')",
                    sql,
                    flags=re.IGNORECASE,
                )
            # Sanitização preventiva para evitar erro 'column "uf" does not exist'
            sql = re.sub(r"\b(?:r|representantes)\.uf\b", "TRIM(SPLIT_PART(r.cidade, '/', 2))", sql, flags=re.IGNORECASE)
            if re.search(r"\b(?:p|pedidos_totvs)\.uf\b", sql, re.IGNORECASE):
                if "clientes" in sql.lower():
                    sql = re.sub(r"\b(?:p|pedidos_totvs)\.uf\b", "c.uf", sql, flags=re.IGNORECASE)
                else:
                    sql = re.sub(r"\b(?:p|pedidos_totvs)\.uf\b", "c.uf", sql, flags=re.IGNORECASE)
                    sql = sql.replace("FROM pedidos_totvs p", "FROM pedidos_totvs p LEFT JOIN clientes c ON c.codigo = p.cliente_codigo")

            # Se a consulta for sobre saldo_atraso de cliente específico, sincroniza ao vivo do TOTVS antes de rodar
            if "saldo_atraso" in sql.lower() and "clientes" in sql.lower():
                match_cli = re.search(r"(?:razao_social|nome_fantasia|codigo)\s+(?:ILIKE|=)\s+'%?([^%']+)%?'", sql, re.IGNORECASE)
                if match_cli:
                    t_cli = match_cli.group(1).strip()
                    try:
                        res_c = supabase.rpc("conexo_executar_leitura", {
                            "query_str": f"SELECT codigo FROM clientes WHERE razao_social ILIKE '%{t_cli}%' OR nome_fantasia ILIKE '%{t_cli}%' OR codigo = '{t_cli}' LIMIT 1"
                        }).execute()
                        if res_c.data and res_c.data[0].get("codigo"):
                            cod_totvs = str(res_c.data[0]["codigo"])
                            from totvs_client import TotvsClient
                            import datetime
                            st = TotvsClient.consultar_estatisticas(cod_totvs)
                            val_atraso = float(st.get("totalInstallmentsDelayed") or 0)
                            now_sync = datetime.datetime.now(datetime.timezone.utc).isoformat()
                            supabase.table("clientes").update({
                                "saldo_atraso": val_atraso,
                                "sincronizado_totvs_em": now_sync,
                                "updated_at": now_sync
                            }).eq("codigo", cod_totvs).execute()
                    except Exception as ex_sync:
                        print(f"[AutoSync] Aviso ao sincronizar TOTVS: {ex_sync}")

        try:
            resp = supabase.rpc("conexo_executar_leitura", {"query_str": sql}).execute()
        except Exception as err:
            err_str = str(err)
            if 'column "uf" does not exist' in err_str or '42703' in err_str:
                sql_fixed = re.sub(r"\b(?:r|p|representantes|pedidos_totvs)\.uf\b", "c.uf", sql, flags=re.IGNORECASE)
                if "JOIN clientes" not in sql_fixed and "FROM clientes" not in sql_fixed:
                    sql_fixed = re.sub(r",\s*(?:[a-zA-Z_]+\.)?uf\b", "", sql_fixed)
                    sql_fixed = re.sub(r"\b(?:[a-zA-Z_]+\.)?uf\s*=\s*'[^']*'\s*(?:AND|OR)?", "", sql_fixed, flags=re.IGNORECASE)
                try:
                    resp = supabase.rpc("conexo_executar_leitura", {"query_str": sql_fixed.strip().rstrip(";")}).execute()
                except Exception:
                    raise err
            elif '42804' in err_str or 'UNION types' in err_str:
                primeiro_select = re.split(r"\bUNION\s+(?:ALL\s+)?", sql, flags=re.IGNORECASE)[0].strip()
                try:
                    resp = supabase.rpc("conexo_executar_leitura", {"query_str": primeiro_select.rstrip(";")}).execute()
                except Exception:
                    raise err
            else:
                raise err
        data = resp.data or []

        # Resiliência para busca de clientes (ex: 'foxs textil' no prompt vs 'FOXSTEXTIL' no banco):
        if not data and sql:
            match = re.search(r"((?:p\.)?(?:cliente_nome|razao_social|nome_fantasia))\s+ILIKE\s+'%([^%']+)%'", sql, re.IGNORECASE)
            if match:
                col, val = match.groups()
                val_limpo = val.strip()
                if " " in val_limpo:
                    val_sem_espaco = val_limpo.replace(" ", "")
                    termo_inicial = val_limpo.split()[0]
                    cond_flex = f"(REPLACE(LOWER({col}), ' ', '') LIKE '%{val_sem_espaco.lower()}%' OR {col} ILIKE '%{termo_inicial}%')"
                    sql_alt = sql.replace(f"{col} ILIKE '%{val}%'", cond_flex).replace(f"{col} ILIKE '%{val_limpo}%'", cond_flex)
                    try:
                        resp_alt = supabase.rpc("conexo_executar_leitura", {"query_str": sql_alt}).execute()
                        if resp_alt.data:
                            return resp_alt.data
                    except Exception:
                        pass

        return data

    # Comparativo Inteligente Proporcional (MTD - Month-to-Date)
    if intent in ("conexo_comparativo_mes", "conexo_comparativo_ano"):
        import datetime
        hoje = datetime.date.today()
        dia_atual = hoje.day
        ano_atual = hoje.year

        str_hoje = hoje.strftime("%Y-%m-%d")
        str_inicio_mes = hoje.replace(day=1).strftime("%Y-%m-%d")

        primeiro_dia_mes = hoje.replace(day=1)
        ultimo_dia_mes_ant = primeiro_dia_mes - datetime.timedelta(days=1)
        str_inicio_mes_ant = ultimo_dia_mes_ant.replace(day=1).strftime("%Y-%m-%d")
        dia_limite_ant = min(dia_atual, ultimo_dia_mes_ant.day)
        str_fim_mes_ant_mtd = ultimo_dia_mes_ant.replace(day=dia_limite_ant).strftime("%Y-%m-%d")
        str_fim_mes_ant_full = ultimo_dia_mes_ant.strftime("%Y-%m-%d")

        try:
            data_ano_ant_mtd = hoje.replace(year=ano_atual - 1)
        except ValueError:
            data_ano_ant_mtd = hoje.replace(year=ano_atual - 1, day=28)
        str_inicio_ano_ant_mtd = data_ano_ant_mtd.replace(day=1).strftime("%Y-%m-%d")
        str_fim_ano_ant_mtd = data_ano_ant_mtd.strftime("%Y-%m-%d")

        sql_mtd = f"""
        SELECT 
            COALESCE(SUM(CASE WHEN nota_fiscal_data::date >= '{str_inicio_mes}' AND nota_fiscal_data::date <= '{str_hoje}' THEN valor_nf ELSE 0 END), 0) AS faturamento_atual_mtd,
            COALESCE(SUM(CASE WHEN nota_fiscal_data::date >= '{str_inicio_mes}' AND nota_fiscal_data::date <= '{str_hoje}' THEN quantidade_total ELSE 0 END), 0) AS metragem_atual_mtd,
            COUNT(CASE WHEN nota_fiscal_data::date >= '{str_inicio_mes}' AND nota_fiscal_data::date <= '{str_hoje}' THEN 1 END) AS pedidos_atual_mtd,

            COALESCE(SUM(CASE WHEN nota_fiscal_data::date >= '{str_inicio_mes_ant}' AND nota_fiscal_data::date <= '{str_fim_mes_ant_mtd}' THEN valor_nf ELSE 0 END), 0) AS faturamento_ant_mtd,
            COALESCE(SUM(CASE WHEN nota_fiscal_data::date >= '{str_inicio_mes_ant}' AND nota_fiscal_data::date <= '{str_fim_mes_ant_mtd}' THEN quantidade_total ELSE 0 END), 0) AS metragem_ant_mtd,

            COALESCE(SUM(CASE WHEN nota_fiscal_data::date >= '{str_inicio_mes_ant}' AND nota_fiscal_data::date <= '{str_fim_mes_ant_full}' THEN valor_nf ELSE 0 END), 0) AS faturamento_ant_full,
            COALESCE(SUM(CASE WHEN nota_fiscal_data::date >= '{str_inicio_mes_ant}' AND nota_fiscal_data::date <= '{str_fim_mes_ant_full}' THEN quantidade_total ELSE 0 END), 0) AS metragem_ant_full,

            COALESCE(SUM(CASE WHEN nota_fiscal_data::date >= '{str_inicio_ano_ant_mtd}' AND nota_fiscal_data::date <= '{str_fim_ano_ant_mtd}' THEN valor_nf ELSE 0 END), 0) AS faturamento_ano_ant_mtd,
            COALESCE(SUM(CASE WHEN nota_fiscal_data::date >= '{str_inicio_ano_ant_mtd}' AND nota_fiscal_data::date <= '{str_fim_ano_ant_mtd}' THEN quantidade_total ELSE 0 END), 0) AS metragem_ano_ant_mtd
        FROM pedidos_totvs
        WHERE status IN ('Attended', 'PartiallyAnswered')
        """
        resp = supabase.rpc("conexo_executar_leitura", {"query_str": sql_mtd}).execute()
        d = resp.data[0] if resp.data else {}

        d["dia_atual"] = dia_atual
        d["dias_mes_anterior"] = dia_limite_ant
        
        fat_atual = float(d.get("faturamento_atual_mtd") or 0)
        d["projecao_fechamento_mes"] = round((fat_atual / dia_atual) * 30, 2) if dia_atual > 0 else 0

        return [d]

    if intent not in RPCS:
        raise ValueError(f"Intent '{intent}' não é uma RPC válida.")

    params = dict(params)

    # Multi-tenant: injeta tenant e rep do TOKEN (nunca do usuário)
    if ctx:
        params["p_tenant"] = ctx["tenant_id"]
        if intent in RPCS_COM_REP:
            params["p_rep"] = ctx.get("rep")  # None = gestor (vê tudo)

    resp = supabase.rpc(intent, params).execute()
    return resp.data
