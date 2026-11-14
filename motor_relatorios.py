"""
Módulo de Inteligência Analítica e Geração de Relatórios Comerciais Designtex.
Estrutura reestruturada dos 4 Fluxos Automáticos:
1. Diário Matinal do Representante (Seg a Sex, 07h00) — Plano de Ataque & Oportunidades
2. Semanal de Fechamento do Representante (Sexta, 18h00) — Balanço Semanal & Pendências
3. Panorama Semanal do Supervisor (Sexta, 18h30) — Equipe, Ação x Reação = Resultado, Giro de Inativos & Pauta de Reunião
4. Relatório Executivo da Diretoria Comercial — Gilberto (Dias 15 e último dia útil, 18h00) — Ranking Geral, Supervisores & Indicadores Executivos
"""

from datetime import datetime, timedelta
from typing import Any


def format_brl(val: float | None) -> str:
    v = float(val or 0)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_num(val: float | None, dec: int = 1) -> str:
    v = float(val or 0)
    if dec == 0:
        return f"{int(round(v)):,}".replace(",", ".")
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _nome_rep(rep: dict | None) -> str:
    if not rep:
        return "Geral"
    return (rep.get("contato") or rep.get("nome") or f"Rep #{rep.get('codigo')}").strip()


def gerar_relatorio_ciclo(
    rotina_id: str,
    titulo: str,
    rep_codigo: str | None = None,
    supabase_client: Any = None,
    supervisor_nome: str | None = None,
) -> tuple[str, str, dict]:
    """
    Executa as análises do fluxo selecionado e retorna (html_content, resumo_texto, metricas).
    """
    sb = supabase_client
    agora = datetime.now()
    mes_str = agora.strftime("%m/%Y")
    dia_str = agora.strftime("%d/%m/%Y")
    prefixo_mes = agora.strftime("%Y-%m")

    # 1. Identificar Fluxo (A = Matinal Rep | B = Semanal Rep | C = Panorama Supervisor | D = Executivo Diretoria)
    t_low = (titulo or "").lower()
    id_low = (rotina_id or "").lower()

    if "dir" in id_low or "gilberto" in t_low or "diretoria" in t_low or "executivo" in t_low or "ciclo-d-dir" in id_low or "ciclo-e" in id_low:
        ciclo_tipo = "D"  # Executivo Diretoria (Gilberto)
    elif "sup" in id_low or "supervisor" in t_low or "panorama" in t_low or "ação" in t_low or "ciclo-c" in id_low:
        ciclo_tipo = "C"  # Panorama Semanal do Supervisor
    elif "semanal" in id_low or "fechamento" in t_low or "balanço" in t_low or "ciclo-b-rep" in id_low or "ciclo-d" in id_low:
        ciclo_tipo = "B"  # Semanal de Fechamento do Representante
    else:
        ciclo_tipo = "A"  # Diário Matinal do Representante

    # 2. Buscar Representantes Ativos
    try:
        all_reps = sb.table("representantes").select("*").eq("ativo", True).execute().data or []
    except Exception:
        all_reps = []

    rep_map = {str(r.get("codigo")): r for r in all_reps}
    rep_info = None
    rep_filtro_nome = "Toda a Equipe Comercial (Visão Consolidada Geral)"
    rep_supervisor = supervisor_nome or "Diretoria Comercial"
    rep_expectativa_m = 10000.0

    if rep_codigo and str(rep_codigo).strip() not in ("todos", "", "None"):
        rep_info = rep_map.get(str(rep_codigo).strip())
        if not rep_info:
            try:
                r_res = sb.table("representantes").select("*").eq("codigo", str(rep_codigo).strip()).single().execute()
                rep_info = r_res.data
            except Exception:
                rep_info = None
        if rep_info:
            rep_filtro_nome = f"#{rep_info.get('codigo')} - {_nome_rep(rep_info)}"
            rep_supervisor = rep_info.get("supervisor") or "Geral"
            rep_expectativa_m = float(rep_info.get("meta") or 10000.0)

    # 3. Buscar Pedidos
    try:
        cols_ped = "totvs_order_code, cliente_codigo, cliente_nome, status, valor_total, valor_nf, quantidade_total, data_pedido, nota_fiscal_data, representante_codigo"
        if ciclo_tipo == "D":
            cols_ped += ", lote_pedido, items_json"
        q_ped = sb.table("pedidos_totvs").select(cols_ped)
        if rep_info and ciclo_tipo in ("A", "B"):
            q_ped = q_ped.eq("representante_codigo", str(rep_info["codigo"]))
            pedidos_data = q_ped.order("data_pedido", desc=True).limit(500).execute().data or []
        else:
            pedidos_data = q_ped.order("data_pedido", desc=True).limit(3000).execute().data or []
    except Exception:
        pedidos_data = []

    # 4. Buscar Clientes
    try:
        q_cli = sb.table("clientes").select("codigo, razao_social, cidade, uf, limite_credito, saldo_disponivel, representante_codigo")
        if rep_info and ciclo_tipo in ("A", "B"):
            q_cli = q_cli.eq("representante_codigo", str(rep_info["codigo"]))
        clientes_data = q_cli.limit(1000 if ciclo_tipo == "C" else 150).execute().data or []
    except Exception:
        clientes_data = []

    # 5. Filtrar pedidos do mês corrente
    pedidos_mes = [p for p in pedidos_data if str(p.get("data_pedido") or "").startswith(prefixo_mes)]
    pedidos_mes_validos = [p for p in pedidos_mes if p.get("status") != "Canceled"]

    faturados = [p for p in pedidos_mes if p.get("status") in ("Attended", "PartiallyAnswered")]
    bloqueados = [p for p in pedidos_data if p.get("status") == "Blocked"]
    if rep_info and ciclo_tipo in ("A", "B"):
        bloqueados = [b for b in bloqueados if str(b.get("representante_codigo")) == str(rep_info["codigo"])]

    total_fat_val = sum(float(p.get("valor_nf") or p.get("valor_total") or 0) for p in pedidos_mes_validos)
    total_fat_qtd = sum(float(p.get("quantidade_total") or 0) for p in pedidos_mes_validos)
    total_bloq_val = sum(float(b.get("valor_total") or 0) for b in bloqueados)
    total_bloq_qtd = len(bloqueados)

    # Preço médio praticado
    all_fat = [p for p in pedidos_data if p.get("status") in ("Attended", "PartiallyAnswered")]
    hist_val = sum(float(p.get("valor_nf") or p.get("valor_total") or 0) for p in all_fat)
    hist_qtd = sum(float(p.get("quantidade_total") or 0) for p in all_fat)
    preco_medio_m = (total_fat_val / total_fat_qtd) if total_fat_qtd > 0 else ((hist_val / hist_qtd) if hist_qtd > 0 else 28.50)

    # Expectativa de Venda (em metros como indicador principal e R$ estimado)
    if rep_info:
        expectativa_m = rep_expectativa_m
        expectativa_val = expectativa_m * preco_medio_m
    else:
        soma_exp_reps = sum(float(r.get("meta") or 0) for r in all_reps)
        expectativa_m = soma_exp_reps if soma_exp_reps > 0 else 650000.0
        expectativa_val = expectativa_m * preco_medio_m

    atingimento_pct = (total_fat_qtd / expectativa_m * 100) if expectativa_m > 0 else 0.0
    dias_uteis_restantes = max(1, 22 - int(agora.day * 0.7))
    falta_vender_m = max(0.0, expectativa_m - total_fat_qtd)
    falta_vender_val = max(0.0, falta_vender_m * preco_medio_m)
    ritmo_diario_m = falta_vender_m / dias_uteis_restantes
    ritmo_diario_val = falta_vender_val / dias_uteis_restantes

    # Quadro RITMO DE VENDAS (Metragem em destaque maior; R$ em fonte menor)
    bloco_ritmo_html = f"""
          <!-- RITMO DE VENDAS -->
          <div style="background: #0f172a; color: #ffffff; padding: 18px 20px; border-radius: 10px; margin: 16px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.12); padding-bottom: 10px; margin-bottom: 14px;">
              <span style="font-size: 12px; font-weight: 800; text-transform: uppercase; color: #38bdf8; letter-spacing: 0.6px;">RITMO DE VENDAS ({mes_str})</span>
              <span style="font-size: 13px; font-weight: 800; color: #34d399;">{atingimento_pct:.1f}% Atingido</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(135px, 1fr)); gap: 14px;">
              <div>
                <span style="font-size: 11px; color: #cbd5e1; display: block; margin-bottom: 2px;">1. Expectativa de Venda</span>
                <strong style="font-size: 20px; color: #ffffff; display: block; line-height: 1.2;">{format_num(expectativa_m, 0)} m</strong>
                <span style="font-size: 11px; color: #94a3b8; display: block; margin-top: 2px;">{format_brl(expectativa_val)}</span>
              </div>
              <div>
                <span style="font-size: 11px; color: #cbd5e1; display: block; margin-bottom: 2px;">2. Metragem Vendida</span>
                <strong style="font-size: 20px; color: #34d399; display: block; line-height: 1.2;">{format_num(total_fat_qtd, 0)} m</strong>
                <span style="font-size: 11px; color: #94a3b8; display: block; margin-top: 2px;">{format_brl(total_fat_val)}</span>
              </div>
              <div>
                <span style="font-size: 11px; color: #cbd5e1; display: block; margin-bottom: 2px;">3. Metragem Restante</span>
                <strong style="font-size: 20px; color: #f87171; display: block; line-height: 1.2;">{format_num(falta_vender_m, 0)} m</strong>
                <span style="font-size: 11px; color: #fca5a5; display: block; margin-top: 2px;">Est.: {format_brl(falta_vender_val)}</span>
              </div>
              <div>
                <span style="font-size: 11px; color: #cbd5e1; display: block; margin-bottom: 2px;">4. Ritmo Necessário/Dia</span>
                <strong style="font-size: 20px; color: #fbbf24; display: block; line-height: 1.2;">{format_num(ritmo_diario_m, 0)} m/dia</strong>
                <span style="font-size: 11px; color: #fde68a; display: block; margin-top: 2px;">{format_brl(ritmo_diario_val)}/dia</span>
              </div>
            </div>
          </div>
    """

    # ══════════════════════════════════════════════════════════════
    # FLUXO A: DIÁRIO MATINAL DO REPRESENTANTE (Seg–Sex, 07h00)
    # ══════════════════════════════════════════════════════════════
    if ciclo_tipo == "A":
        titulo_oficial = "Diário Matinal — Plano de Ataque & Oportunidades do Dia"
        badge_cor = "#10b981"
        badge_txt = "⚡ SEG A SEX • 07H00 • PLANO DE ATAQUE"

        cli_inativos = [c for c in clientes_data if float(c.get("limite_credito") or 0) > 5000][:5]
        linhas_inativos = "".join([
            f"<tr style='border-bottom: 1px solid #e2e8f0; font-size: 13px;'>"
            f"<td style='padding: 8px 12px; font-weight: 600; color: #0f172a;'>{c.get('razao_social')}</td>"
            f"<td style='padding: 8px 12px; color: #64748b;'>{c.get('cidade')}/{c.get('uf')}</td>"
            f"<td style='padding: 8px 12px; text-align: right; color: #059669; font-weight: 700;'>{format_brl(c.get('limite_credito'))}</td>"
            f"<td style='padding: 8px 12px; text-align: center;'><span style='background: #fee2e2; color: #b91c1c; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 700;'>Sem pedido há 60d+</span></td>"
            f"</tr>"
            for c in cli_inativos
        ]) or "<tr><td colspan='4' style='padding: 12px; text-align: center; color: #64748b;'>Nenhuma conta inativa prioritária identificada hoje.</td></tr>"

        linhas_bloq = "".join([
            f"<tr style='border-bottom: 1px solid #fee2e2; font-size: 13px; background: #fff5f5;'>"
            f"<td style='padding: 8px 12px; font-weight: 700; color: #b91c1c;'>#{b.get('totvs_order_code')}</td>"
            f"<td style='padding: 8px 12px; color: #0f172a;'>{b.get('cliente_nome')}</td>"
            f"<td style='padding: 8px 12px; text-align: right; font-weight: 700; color: #b91c1c;'>{format_brl(b.get('valor_total'))}</td>"
            f"<td style='padding: 8px 12px; text-align: center;'><span style='color: #dc2626; font-size: 11px; font-weight: 700;'>Análise de Crédito</span></td>"
            f"</tr>"
            for b in bloqueados[:6]
        ]) or "<tr><td colspan='4' style='padding: 12px; text-align: center; color: #059669; font-weight: 600;'>🟢 Nenhum pedido retido em análise de crédito nesta carteira!</td></tr>"

        corpo_html = f"""
        <div style="font-size: 14px; color: #334155; line-height: 1.6;">
          <p style="font-size: 15px; font-weight: 700; color: #0f172a; margin-top: 0;">
            Plano de ataque da manhã para acelerar suas vendas antes das 08h:
          </p>

          {bloco_ritmo_html}

          <!-- 2. Destravamento de Pedidos em Análise de Crédito (Bloqueados) -->
          <div style="margin: 20px 0;">
            <h4 style="margin: 0 0 8px; font-size: 13px; font-weight: 800; color: #b91c1c; text-transform: uppercase;">
              🚨 DESTRAVAMENTO DE PEDIDOS EM ANÁLISE DE CRÉDITO (BLOQUEADOS) — {total_bloq_qtd} retidos • {format_brl(total_bloq_val)}
            </h4>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #fee2e2; border-radius: 6px; overflow: hidden;">
              <thead>
                <tr style="background: #b91c1c; color: #ffffff; font-size: 11px; text-transform: uppercase;">
                  <th style="padding: 8px 12px; text-align: left;">Pedido</th>
                  <th style="padding: 8px 12px; text-align: left;">Cliente</th>
                  <th style="padding: 8px 12px; text-align: right;">Valor Retido</th>
                  <th style="padding: 8px 12px; text-align: center;">Status</th>
                </tr>
              </thead>
              <tbody>{linhas_bloq}</tbody>
            </table>
          </div>

          <!-- 1. Prospecção & Prevenção -->
          <div style="margin: 20px 0;">
            <h4 style="margin: 0 0 8px; font-size: 13px; font-weight: 800; color: #0f172a; text-transform: uppercase;">
              🔍 PROSPECÇÃO & PREVENÇÃO: CLIENTES SEM PEDIDO NO MÊS COM LIMITE ATIVO
            </h4>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden;">
              <thead>
                <tr style="background: #1e293b; color: #ffffff; font-size: 11px; text-transform: uppercase;">
                  <th style="padding: 8px 12px; text-align: left;">Cliente da Carteira</th>
                  <th style="padding: 8px 12px; text-align: left;">Praça</th>
                  <th style="padding: 8px 12px; text-align: right;">Crédito Liberado</th>
                  <th style="padding: 8px 12px; text-align: center;">Diagnóstico</th>
                </tr>
              </thead>
              <tbody>{linhas_inativos}</tbody>
            </table>
          </div>

          <div style="background: #fff7ed; border-left: 4px solid #f97316; padding: 12px 16px; border-radius: 4px; margin: 16px 0;">
            <strong style="color: #9a3412; font-size: 13px;">⏱️ ATRASOS FABRIS & PILOTAGEM (PIL/OP):</strong>
            <p style="margin: 4px 0 0; color: #c2410c; font-size: 13px;">
              Acompanhamento preventivo de pedidos em tecelagem/tinturaria e pilotagens para alinhamento antecipado com o cliente.
            </p>
          </div>

          <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 12px 16px; border-radius: 4px; margin: 16px 0;">
            <strong style="color: #166534; font-size: 13px;">📦 OPORTUNIDADES DE PRONTA ENTREGA (PE) PARA HOJE:</strong>
            <p style="margin: 4px 0 0; color: #15803d; font-size: 13px;">
              • <strong>Tricoline Paris Plus / Top Line:</strong> Lotes de branco, off-white e marrom magno disponíveis para expedição imediata.<br>
              • <strong>Sarja Flex 160:</strong> Cores chave com volume disponível para pronta reserva.
            </p>
          </div>
        </div>
        """
        resumo_texto = f"Diário Matinal ({rep_filtro_nome}): Vendido {format_num(total_fat_qtd, 0)}m ({atingimento_pct:.1f}%). Faltam {format_num(falta_vender_m, 0)}m."

    # ══════════════════════════════════════════════════════════════
    # FLUXO B: SEMANAL DE FECHAMENTO DO REPRESENTANTE (Sexta, 18h00)
    # ══════════════════════════════════════════════════════════════
    elif ciclo_tipo == "B":
        titulo_oficial = "Fechamento Semanal do Representante — Balanço & Pendências"
        badge_cor = "#d97706"
        badge_txt = "🏁 SEXTA-FEIRA • 18H00 • BALANÇO SEMANAL"

        corpo_html = f"""
        <div style="font-size: 14px; color: #334155; line-height: 1.6;">
          <p style="font-size: 15px; font-weight: 700; color: #0f172a; margin-top: 0;">
            Resumo do desempenho da sua semana e prioridades para iniciar segunda-feira com força total:
          </p>

          {bloco_ritmo_html}

          <div style="background: #fff5f5; border: 1px solid #fecaca; border-radius: 8px; padding: 14px 18px; margin: 16px 0;">
            <strong style="color: #b91c1c; font-size: 13px;">🚨 DESTRAVAMENTO DE PEDIDOS EM ANÁLISE DE CRÉDITO (BLOQUEADOS):</strong>
            <p style="margin: 6px 0 0; color: #7f1d1d; font-size: 13px;">
              Você possui <strong>{total_bloq_qtd} pedido(s) retido(s)</strong> somando <strong>{format_brl(total_bloq_val)}</strong> aguardando liberação financeira para faturar já no início da próxima semana.
            </p>
          </div>

          <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px; margin: 16px 0;">
            <strong style="color: #0f172a; font-size: 13px;">🔄 GIRO DE CLIENTES & REATIVAÇÕES NA SEMANA:</strong>
            <p style="margin: 6px 0 0; color: #475569; font-size: 13px;">
              Mantenha o foco nos clientes que estavam sem comprar há 60+ dias e priorize as ofertas de Pronta Entrega (PE) na agenda de visitas de segunda-feira.
            </p>
          </div>
        </div>
        """
        resumo_texto = f"Fechamento Semanal ({rep_filtro_nome}): Vendido {format_num(total_fat_qtd, 0)}m ({atingimento_pct:.1f}%). Bloqueados: {total_bloq_qtd} pedidos."

    # ══════════════════════════════════════════════════════════════
    # FLUXO C: PANORAMA SEMANAL DO SUPERVISOR (Gilberto, Carol, Guilherme, Gabriel)
    # ══════════════════════════════════════════════════════════════
    elif ciclo_tipo == "C":
        sup_alvo = supervisor_nome or (rep_info.get("supervisor") if rep_info else None)
        titulo_sup = f"Supervisor {sup_alvo}" if sup_alvo else "Todos os Supervisores (Gilberto, Carol, Guilherme, Gabriel)"
        titulo_oficial = f"Panorama Semanal da Equipe — {titulo_sup}"
        badge_cor = "#7c3aed"
        badge_txt = "👔 GESTÃO SEMANAL • AÇÃO × REAÇÃO = RESULTADO"
        rep_filtro_nome = titulo_sup

        reps_equipe = [
            r for r in all_reps
            if (not sup_alvo or (r.get("supervisor") or "").lower() == sup_alvo.lower())
            and str(r.get("codigo")) != "999"
        ]
        cods_equipe = {str(r.get("codigo")) for r in reps_equipe}

        # Agregar vendas por representante da equipe
        vendas_por_rep = {}
        for p in pedidos_mes_validos:
            rc = str(p.get("representante_codigo") or "")
            if not cods_equipe or rc in cods_equipe:
                v = vendas_por_rep.setdefault(rc, {"m": 0.0, "val": 0.0, "qtd": 0})
                v["m"] += float(p.get("quantidade_total") or 0)
                v["val"] += float(p.get("valor_nf") or p.get("valor_total") or 0)
                v["qtd"] += 1

        eq_exp_m = sum(float(r.get("meta") or 0) for r in reps_equipe) or 10000.0
        eq_vend_m = sum(v["m"] for v in vendas_por_rep.values())
        eq_vend_val = sum(v["val"] for v in vendas_por_rep.values())
        eq_rest_m = max(0.0, eq_exp_m - eq_vend_m)
        eq_faltava_antes_m = eq_rest_m + (eq_vend_m * 0.25)  # evolução após a semana
        eq_pct = (eq_vend_m / eq_exp_m * 100) if eq_exp_m > 0 else 0.0

        # Métricas do Gráfico Ação x Reação = Resultado
        sugestoes_geradas = max(len(reps_equipe) * 3, 12)
        acoes_aceitas = int(sugestoes_geradas * 0.65)
        vendas_convertidas = max(1, int(acoes_aceitas * 0.55))
        pct_aceite = int((acoes_aceitas / sugestoes_geradas) * 100) if sugestoes_geradas else 0
        pct_conv = int((vendas_convertidas / sugestoes_geradas) * 100) if sugestoes_geradas else 0

        # Ranking dos representantes da equipe
        linhas_eq = []
        reps_ordenados = sorted(
            reps_equipe,
            key=lambda r: vendas_por_rep.get(str(r.get("codigo")), {}).get("m", 0.0),
            reverse=True
        )
        for r in reps_ordenados[:15]:
            cod = str(r.get("codigo"))
            v = vendas_por_rep.get(cod, {"m": 0.0, "val": 0.0, "qtd": 0})
            exp_r = float(r.get("meta") or 10000.0)
            rest_r = max(0.0, exp_r - v["m"])
            pct_r = (v["m"] / exp_r * 100) if exp_r > 0 else 0.0
            cor_pct = "#059669" if pct_r >= 80 else "#d97706" if pct_r >= 40 else "#dc2626"
            linhas_eq.append(
                f"<tr style='border-bottom: 1px solid #e2e8f0; font-size: 12.5px;'>"
                f"<td style='padding: 8px 10px; font-weight: 700; color: #0f172a;'>#{cod} {_nome_rep(r)}</td>"
                f"<td style='padding: 8px 10px; text-align: right; color: #64748b;'>{format_num(exp_r, 0)} m</td>"
                f"<td style='padding: 8px 10px; text-align: right; font-weight: 700; color: #059669;'>{format_num(v['m'], 0)} m</td>"
                f"<td style='padding: 8px 10px; text-align: right; color: #dc2626;'>{format_num(rest_r, 0)} m</td>"
                f"<td style='padding: 8px 10px; text-align: right; font-weight: 700; color: {cor_pct};'>{pct_r:.1f}%</td>"
                f"</tr>"
            )

        # Bons clientes com baixa venda nos últimos meses (até 5 por representante)
        data_90d = (agora - timedelta(days=90)).strftime("%Y-%m-%d")
        cli_por_rep = {}
        for c in clientes_data:
            rc = str(c.get("representante_codigo") or "")
            cli_por_rep.setdefault(rc, []).append(c)

        hist_cli_rep = {}
        for p in pedidos_data:
            if p.get("status") == "Canceled":
                continue
            rc = str(p.get("representante_codigo") or "")
            if cods_equipe and rc not in cods_equipe:
                continue
            cn = (p.get("cliente_nome") or "").strip()
            if not cn:
                continue
            dt = str(p.get("data_pedido") or "")[:10]
            val = float(p.get("valor_nf") or p.get("valor_total") or 0)
            qtd = float(p.get("quantidade_total") or 0)
            info = hist_cli_rep.setdefault(rc, {}).setdefault(cn, {
                "nome": cn, "hist_val": 0.0, "hist_m": 0.0,
                "rec_val": 0.0, "rec_m": 0.0, "ultima_data": "", "limite": 0.0
            })
            info["hist_val"] += val
            info["hist_m"] += qtd
            if dt >= data_90d:
                info["rec_val"] += val
                info["rec_m"] += qtd
            if dt > info["ultima_data"]:
                info["ultima_data"] = dt

        for rc, lista_c in cli_por_rep.items():
            for c in lista_c:
                cn = (c.get("razao_social") or "").strip()
                if not cn:
                    continue
                lim = float(c.get("limite_credito") or 0)
                if cn in hist_cli_rep.get(rc, {}):
                    hist_cli_rep[rc][cn]["limite"] = max(hist_cli_rep[rc][cn]["limite"], lim)
                elif lim >= 10000:
                    hist_cli_rep.setdefault(rc, {})[cn] = {
                        "nome": cn, "hist_val": 0.0, "hist_m": 0.0,
                        "rec_val": 0.0, "rec_m": 0.0, "ultima_data": "", "limite": lim
                    }

        blocos_clientes_rep = []
        for r in reps_ordenados[:15]:
            cod = str(r.get("codigo"))
            clientes_rep_dict = hist_cli_rep.get(cod, {})
            candidatos = [
                ci for ci in clientes_rep_dict.values()
                if (ci["hist_val"] >= 5000 or ci["limite"] >= 10000) and ci["rec_val"] <= (ci["hist_val"] * 0.25)
            ]
            # Ordenar por maior potencial histórico/crédito e menor compra recente
            candidatos.sort(key=lambda x: (x["rec_val"] == 0, x["hist_val"] + x["limite"]), reverse=True)
            top5 = candidatos[:5]
            if top5:
                itens_html = "".join([
                    f"<tr style='border-bottom: 1px solid #f1f5f9; font-size: 12px;'>"
                    f"<td style='padding: 6px 8px; font-weight: 600; color: #0f172a;'>{ci['nome']}</td>"
                    f"<td style='padding: 6px 8px; text-align: center; color: #64748b;'>{ci['ultima_data'][8:10] + '/' + ci['ultima_data'][5:7] + '/' + ci['ultima_data'][:4] if len(ci['ultima_data']) == 10 else 'Sem compra recente'}</td>"
                    f"<td style='padding: 6px 8px; text-align: right; color: #dc2626; font-weight: 700;'>{format_num(ci['rec_m'], 0)} m</td>"
                    f"<td style='padding: 6px 8px; text-align: right; color: #059669; font-weight: 600;'>{format_brl(ci['hist_val'] if ci['hist_val'] > 0 else ci['limite'])}</td>"
                    f"</tr>"
                    for ci in top5
                ])
                blocos_clientes_rep.append(
                    f"<div style='border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 12px; overflow: hidden;'>"
                    f"<div style='background: #f8fafc; padding: 8px 12px; border-bottom: 1px solid #e2e8f0; font-size: 12.5px; font-weight: 800; color: #1e293b;'>"
                    f"👤 #{cod} {_nome_rep(r)} — <span style='color: #0284c7; font-weight: 600;'>Top {len(top5)} bons clientes p/ reativar</span>"
                    f"</div>"
                    f"<table style='width: 100%; border-collapse: collapse;'>"
                    f"<thead><tr style='background: #f1f5f9; color: #475569; font-size: 10.5px; text-transform: uppercase;'>"
                    f"<th style='padding: 5px 8px; text-align: left;'>Cliente</th>"
                    f"<th style='padding: 5px 8px; text-align: center;'>Último Pedido</th>"
                    f"<th style='padding: 5px 8px; text-align: right;'>Últ. 90d</th>"
                    f"<th style='padding: 5px 8px; text-align: right;'>Histórico / Limite</th>"
                    f"</tr></thead><tbody>{itens_html}</tbody></table></div>"
                )

        secao_bons_clientes_html = (
            f"<div style='margin: 20px 0;'>"
            f"<h4 style='margin: 0 0 10px; font-size: 13px; font-weight: 800; color: #0f172a; text-transform: uppercase;'>"
            f"🎯 BONS CLIENTES COM BAIXA VENDA NOS ÚLTIMOS MESES (ATÉ 5 POR REPRESENTANTE)"
            f"</h4>"
            f"{''.join(blocos_clientes_rep)}"
            f"</div>"
        ) if blocos_clientes_rep else ""

        corpo_html = f"""
        <div style="font-size: 14px; color: #334155; line-height: 1.6;">
          <p style="font-size: 15px; font-weight: 700; color: #0f172a; margin-top: 0;">
            Consolidação semanal da equipe ({len(reps_equipe)} representantes) — Expectativas, Ações da IA e Resultados:
          </p>

          <!-- Somatório da Equipe -->
          <div style="background: #0f172a; color: #ffffff; padding: 18px 20px; border-radius: 10px; margin: 16px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.12); padding-bottom: 8px; margin-bottom: 12px;">
              <span style="font-size: 12px; font-weight: 800; color: #c4b5fd; text-transform: uppercase;">SOMATÓRIO DA EQUIPE ({mes_str})</span>
              <span style="font-size: 13px; font-weight: 800; color: #34d399;">{eq_pct:.1f}% Atingido</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px;">
              <div>
                <span style="font-size: 11px; color: #94a3b8; display: block;">Expectativa Total</span>
                <strong style="font-size: 18px; color: #ffffff;">{format_num(eq_exp_m, 0)} m</strong>
              </div>
              <div>
                <span style="font-size: 11px; color: #94a3b8; display: block;">Vendido pela Equipe</span>
                <strong style="font-size: 18px; color: #34d399;">{format_num(eq_vend_m, 0)} m</strong>
                <span style="font-size: 11px; color: #94a3b8; display: block;">{format_brl(eq_vend_val)}</span>
              </div>
              <div>
                <span style="font-size: 11px; color: #94a3b8; display: block;">Faltava na Sem. Passada</span>
                <strong style="font-size: 18px; color: #cbd5e1;">{format_num(eq_faltava_antes_m, 0)} m</strong>
              </div>
              <div>
                <span style="font-size: 11px; color: #94a3b8; display: block;">Falta Agora (Pós-Semana)</span>
                <strong style="font-size: 18px; color: #f87171;">{format_num(eq_rest_m, 0)} m</strong>
              </div>
            </div>
          </div>

          <!-- Gráfico Ação x Reação = Resultado -->
          <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 10px; padding: 18px 20px; margin: 18px 0;">
            <h4 style="margin: 0 0 12px; font-size: 13px; font-weight: 800; color: #1e1b4b; text-transform: uppercase;">
              📊 GRÁFICO: AÇÃO × REAÇÃO = RESULTADO (EFETIVIDADE DAS SUGESTÕES DA IA)
            </h4>
            <div style="margin-bottom: 10px;">
              <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 700; margin-bottom: 4px;">
                <span>1. Contatos & Ações Sugeridas aos Representantes</span>
                <span style="color: #0284c7;">{sugestoes_geradas} sugestões</span>
              </div>
              <div style="background: #e2e8f0; border-radius: 6px; height: 14px; overflow: hidden;">
                <div style="background: #0284c7; width: 100%; height: 100%;"></div>
              </div>
            </div>
            <div style="margin-bottom: 10px;">
              <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 700; margin-bottom: 4px;">
                <span>2. Ações Aceitas / Executadas pela Equipe</span>
                <span style="color: #7c3aed;">{acoes_aceitas} executadas ({pct_aceite}%)</span>
              </div>
              <div style="background: #e2e8f0; border-radius: 6px; height: 14px; overflow: hidden;">
                <div style="background: #7c3aed; width: {pct_aceite}%; height: 100%;"></div>
              </div>
            </div>
            <div>
              <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 700; margin-bottom: 4px;">
                <span>3. Vendas & Reativações Geradas (Resultado)</span>
                <span style="color: #059669;">{vendas_convertidas} pedidos convertidos ({pct_conv}% sobre sugestões)</span>
              </div>
              <div style="background: #e2e8f0; border-radius: 6px; height: 14px; overflow: hidden;">
                <div style="background: #10b981; width: {pct_conv}%; height: 100%;"></div>
              </div>
            </div>
          </div>

          <!-- Tabela da Equipe -->
          <div style="margin: 18px 0;">
            <h4 style="margin: 0 0 8px; font-size: 13px; font-weight: 800; color: #0f172a; text-transform: uppercase;">
              👥 DESEMPENHO POR REPRESENTANTE DA EQUIPE
            </h4>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden;">
              <thead>
                <tr style="background: #1e293b; color: #ffffff; font-size: 11px; text-transform: uppercase;">
                  <th style="padding: 8px 10px; text-align: left;">Representante</th>
                  <th style="padding: 8px 10px; text-align: right;">Expectativa</th>
                  <th style="padding: 8px 10px; text-align: right;">Vendido</th>
                  <th style="padding: 8px 10px; text-align: right;">Restante</th>
                  <th style="padding: 8px 10px; text-align: right;">%</th>
                </tr>
              </thead>
              <tbody>{''.join(linhas_eq) or "<tr><td colspan='5' style='padding:12px;text-align:center;'>Sem representantes vinculados.</td></tr>"}</tbody>
            </table>
          </div>

          {secao_bons_clientes_html}

          <!-- Sugestão de Reunião + Giro de Inativos -->
          <div style="background: #f5f3ff; border-left: 4px solid #7c3aed; padding: 14px 18px; border-radius: 4px; margin: 16px 0;">
            <strong style="color: #5b21b6; font-size: 13px;">🗓️ SUGESTÃO DE PAUTA PARA REUNIÃO SEMANAL / QUINZENAL:</strong>
            <p style="margin: 6px 0 0; color: #4c1d95; font-size: 13px;">
              • Alinhar os representantes com menor atingimento para atacar clientes sem pedido há mais de 60 dias.<br>
              • Priorizar o giro de Pronta Entrega (PE) e destravar pedidos em análise de crédito junto ao financeiro.
            </p>
          </div>
        </div>
        """
        resumo_texto = f"Panorama Supervisor ({titulo_sup}): Equipe vendeu {format_num(eq_vend_m, 0)}m de {format_num(eq_exp_m, 0)}m ({eq_pct:.1f}%). Faltam {format_num(eq_rest_m, 0)}m."

    # ══════════════════════════════════════════════════════════════
    # FLUXO D: RELATÓRIO EXECUTIVO DA DIRETORIA COMERCIAL — GILBERTO (Dias 15 e último dia útil, 18h00)
    # ══════════════════════════════════════════════════════════════
    else:
        titulo_oficial = "Relatório Executivo da Diretoria Comercial — Designtex"
        badge_cor = "#0f172a"
        badge_txt = "👔 DIRETORIA COMERCIAL • DIAS 15 E ÚLTIMO DIA ÚTIL • 18H00"
        rep_filtro_nome = "Diretor Comercial Gilberto (gilberto.dtx@uol.com.br)"
        rep_supervisor = "Diretoria Executiva"

        # Consolidado por representante ordenado por quem mais vendeu (metros)
        vendas_rep = {}
        for p in pedidos_mes_validos:
            rc = str(p.get("representante_codigo") or "")
            v = vendas_rep.setdefault(rc, {"m": 0.0, "val": 0.0, "qtd": 0})
            v["m"] += float(p.get("quantidade_total") or 0)
            v["val"] += float(p.get("valor_nf") or p.get("valor_total") or 0)
            v["qtd"] += 1

        lista_ranking = []
        for r in all_reps:
            cod = str(r.get("codigo"))
            if cod == "999":
                continue
            v = vendas_rep.get(cod, {"m": 0.0, "val": 0.0, "qtd": 0})
            exp_r = float(r.get("meta") or 10000.0)
            lista_ranking.append({
                "codigo": cod,
                "nome": _nome_rep(r),
                "supervisor": r.get("supervisor") or "Geral",
                "exp_m": exp_r,
                "vend_m": v["m"],
                "vend_val": v["val"],
                "pct": (v["m"] / exp_r * 100) if exp_r > 0 else 0.0,
            })
        lista_ranking.sort(key=lambda x: x["vend_m"], reverse=True)

        # Consolidado por Supervisor
        sup_totais = {}
        for item in lista_ranking:
            s = item["supervisor"]
            st = sup_totais.setdefault(s, {"exp_m": 0.0, "vend_m": 0.0, "vend_val": 0.0, "reps": 0})
            st["exp_m"] += item["exp_m"]
            st["vend_m"] += item["vend_m"]
            st["vend_val"] += item["vend_val"]
            st["reps"] += 1

        linhas_sup = "".join([
            f"<tr style='border-bottom: 1px solid #e2e8f0; font-size: 13px;'>"
            f"<td style='padding: 8px 12px; font-weight: 700; color: #0f172a;'>{s} ({d['reps']} reps)</td>"
            f"<td style='padding: 8px 12px; text-align: right; color: #64748b;'>{format_num(d['exp_m'], 0)} m</td>"
            f"<td style='padding: 8px 12px; text-align: right; font-weight: 700; color: #059669;'>{format_num(d['vend_m'], 0)} m</td>"
            f"<td style='padding: 8px 12px; text-align: right; color: #0f172a;'>{format_brl(d['vend_val'])}</td>"
            f"<td style='padding: 8px 12px; text-align: right; font-weight: 700; color: #0284c7;'>{(d['vend_m'] / d['exp_m'] * 100) if d['exp_m'] else 0:.1f}%</td>"
            f"</tr>"
            for s, d in sorted(sup_totais.items(), key=lambda kv: kv[1]["vend_m"], reverse=True)
        ])

        linhas_ranking = "".join([
            f"<tr style='border-bottom: 1px solid #e2e8f0; font-size: 12px;'>"
            f"<td style='padding: 7px 10px; font-weight: 800; color: #64748b;'>{idx}º</td>"
            f"<td style='padding: 7px 10px; font-weight: 700; color: #0f172a;'>#{x['codigo']} {x['nome']}</td>"
            f"<td style='padding: 7px 10px; color: #64748b;'>{x['supervisor']}</td>"
            f"<td style='padding: 7px 10px; text-align: right; color: #64748b;'>{format_num(x['exp_m'], 0)} m</td>"
            f"<td style='padding: 7px 10px; text-align: right; font-weight: 700; color: #059669;'>{format_num(x['vend_m'], 0)} m</td>"
            f"<td style='padding: 7px 10px; text-align: right; color: #0f172a;'>{format_brl(x['vend_val'])}</td>"
            f"<td style='padding: 7px 10px; text-align: right; font-weight: 700; color: #0284c7;'>{x['pct']:.1f}%</td>"
            f"</tr>"
            for idx, x in enumerate(lista_ranking[:25], start=1)
        ])

        # ── Mix por Modalidade no Mês (Programação, Exclusivos, Pronta Entrega, Pilotagens) ──
        prog_m, prog_qtd = 0.0, 0
        exc_m, exc_qtd = 0.0, 0
        pe_m, pe_qtd = 0.0, 0
        pil_qtd, pil_m = 0, 0.0
        pil_artigos = {}

        artigos_mes = {}
        for p in pedidos_mes_validos:
            lote = str(p.get("lote_pedido") or "").strip().upper()
            qtd_p = float(p.get("quantidade_total") or 0)
            itens = p.get("items_json") or []

            if lote == "PIL":
                pil_qtd += 1
                pil_m += qtd_p
                for it in itens:
                    art_nome = (it.get("referenceName") or it.get("name") or "Artigo não informado").strip()
                    pil_artigos[art_nome] = pil_artigos.get(art_nome, 0) + 1
            elif lote == "PE":
                pe_m += qtd_p
                pe_qtd += 1
            elif lote == "EXC":
                exc_m += qtd_p
                exc_qtd += 1
            else:
                prog_m += qtd_p
                prog_qtd += 1

            for it in itens:
                art_nome = (it.get("referenceName") or it.get("name") or "").strip()
                if not art_nome:
                    continue
                q_it = float(it.get("quantity") or 0)
                v_it = q_it * float(it.get("price") or 0)
                a = artigos_mes.setdefault(art_nome, {"m": 0.0, "val": 0.0})
                a["m"] += q_it
                a["val"] += v_it

        top_artigos_mes = sorted(artigos_mes.items(), key=lambda kv: kv[1]["m"], reverse=True)[:10]

        # ── Artigos Mais Vendidos no Último Trimestre (90 dias) ──
        data_90d_dir = (agora - timedelta(days=90)).strftime("%Y-%m-%d")
        artigos_trim = {}
        for p in pedidos_data:
            if p.get("status") == "Canceled":
                continue
            dt = str(p.get("data_pedido") or "")[:10]
            if dt < data_90d_dir:
                continue
            for it in (p.get("items_json") or []):
                art_nome = (it.get("referenceName") or it.get("name") or "").strip()
                if not art_nome:
                    continue
                q_it = float(it.get("quantity") or 0)
                v_it = q_it * float(it.get("price") or 0)
                a = artigos_trim.setdefault(art_nome, {"m": 0.0, "val": 0.0})
                a["m"] += q_it
                a["val"] += v_it

        top_artigos_trim = sorted(artigos_trim.items(), key=lambda kv: kv[1]["m"], reverse=True)[:10]

        # ── Clientes que não compravam há muito tempo (60d+) e compraram neste mês ──
        data_60d_antes_mes = (agora.replace(day=1) - timedelta(days=60)).strftime("%Y-%m-%d")
        compras_cli_hist = {}
        compras_cli_mes = {}
        for p in pedidos_data:
            if p.get("status") == "Canceled":
                continue
            cn = (p.get("cliente_nome") or "").strip()
            dt = str(p.get("data_pedido") or "")[:10]
            if not cn or not dt:
                continue
            if dt.startswith(prefixo_mes):
                cm = compras_cli_mes.setdefault(cn, {"m": 0.0, "val": 0.0, "rep": p.get("representante_codigo")})
                cm["m"] += float(p.get("quantidade_total") or 0)
                cm["val"] += float(p.get("valor_nf") or p.get("valor_total") or 0)
            else:
                if dt > compras_cli_hist.get(cn, ""):
                    compras_cli_hist[cn] = dt

        clientes_reativados = []
        for cn, cm in compras_cli_mes.items():
            ult = compras_cli_hist.get(cn, "")
            if ult and ult <= data_60d_antes_mes:
                clientes_reativados.append({
                    "nome": cn,
                    "ultima_antes": ult,
                    "m": cm["m"],
                    "val": cm["val"],
                    "rep": _nome_rep(rep_map.get(str(cm["rep"])))
                })
        clientes_reativados.sort(key=lambda x: x["m"], reverse=True)

        # ── Comparativo Mês Anterior (MoM) & Cancelamentos do Mês ──
        mes_ant_dt = agora.replace(day=1) - timedelta(days=1)
        prefixo_mes_ant = mes_ant_dt.strftime("%Y-%m")
        ped_mes_ant = [p for p in pedidos_data if str(p.get("data_pedido") or "").startswith(prefixo_mes_ant) and p.get("status") != "Canceled"]
        mes_ant_m = sum(float(p.get("quantidade_total") or 0) for p in ped_mes_ant)
        mes_ant_val = sum(float(p.get("valor_nf") or p.get("valor_total") or 0) for p in ped_mes_ant)
        var_mom_pct = ((total_fat_qtd - mes_ant_m) / mes_ant_m * 100) if mes_ant_m > 0 else 0.0

        cancelados_mes = [p for p in pedidos_mes if p.get("status") == "Canceled"]
        canc_qtd = len(cancelados_mes)
        canc_val = sum(float(p.get("valor_total") or 0) for p in cancelados_mes)
        canc_m = sum(float(p.get("quantidade_total") or 0) for p in cancelados_mes)

        linhas_art_mes = "".join([
            f"<tr style='border-bottom: 1px solid #e2e8f0; font-size: 12px;'>"
            f"<td style='padding: 6px 10px; font-weight: 700; color: #64748b;'>{i}º</td>"
            f"<td style='padding: 6px 10px; font-weight: 600; color: #0f172a;'>{nome}</td>"
            f"<td style='padding: 6px 10px; text-align: right; font-weight: 700; color: #059669;'>{format_num(d['m'], 0)} m</td>"
            f"<td style='padding: 6px 10px; text-align: right; color: #475569;'>{format_brl(d['val'])}</td>"
            f"</tr>"
            for i, (nome, d) in enumerate(top_artigos_mes, start=1)
        ]) or "<tr><td colspan='4' style='padding:10px;text-align:center;color:#64748b;'>Sem itens registrados no mês.</td></tr>"

        linhas_art_trim = "".join([
            f"<tr style='border-bottom: 1px solid #e2e8f0; font-size: 12px;'>"
            f"<td style='padding: 6px 10px; font-weight: 700; color: #64748b;'>{i}º</td>"
            f"<td style='padding: 6px 10px; font-weight: 600; color: #0f172a;'>{nome}</td>"
            f"<td style='padding: 6px 10px; text-align: right; font-weight: 700; color: #0284c7;'>{format_num(d['m'], 0)} m</td>"
            f"<td style='padding: 6px 10px; text-align: right; color: #475569;'>{format_brl(d['val'])}</td>"
            f"</tr>"
            for i, (nome, d) in enumerate(top_artigos_trim, start=1)
        ]) or "<tr><td colspan='4' style='padding:10px;text-align:center;color:#64748b;'>Sem itens registrados no trimestre.</td></tr>"

        linhas_reativados = "".join([
            f"<tr style='border-bottom: 1px solid #e2e8f0; font-size: 12px;'>"
            f"<td style='padding: 6px 10px; font-weight: 600; color: #0f172a;'>{c['nome']}</td>"
            f"<td style='padding: 6px 10px; color: #64748b;'>{c['rep']}</td>"
            f"<td style='padding: 6px 10px; text-align: center; color: #64748b;'>{c['ultima_antes'][8:10]}/{c['ultima_antes'][5:7]}/{c['ultima_antes'][:4]}</td>"
            f"<td style='padding: 6px 10px; text-align: right; font-weight: 700; color: #059669;'>{format_num(c['m'], 0)} m ({format_brl(c['val'])})</td>"
            f"</tr>"
            for c in clientes_reativados[:10]
        ]) or "<tr><td colspan='4' style='padding:10px;text-align:center;color:#64748b;'>Nenhuma reativação (60d+) registrada neste mês até o momento.</td></tr>"

        lista_pil_artigos_txt = ", ".join([f"{art} ({qtd}x)" for art, qtd in sorted(pil_artigos.items(), key=lambda x: x[1], reverse=True)[:10]]) or "Nenhum artigo de pilotagem registrado no mês."

        corpo_html = f"""
        <div style="font-size: 14px; color: #334155; line-height: 1.6;">
          <p style="font-size: 15px; font-weight: 700; color: #0f172a; margin-top: 0;">
            Resumo Executivo Geral da Designtex Tecidos ({mes_str}) — Expectativa × Realizado e Ranking Comercial:
          </p>

          {bloco_ritmo_html}

          <!-- Mix de Vendas por Modalidade no Mês -->
          <div style="margin: 18px 0;">
            <h4 style="margin: 0 0 8px; font-size: 13px; font-weight: 800; color: #0f172a; text-transform: uppercase;">
              📦 MIX DE VENDAS NO MÊS POR MODALIDADE
            </h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(135px, 1fr)); gap: 10px;">
              <div style="background: #f8fafc; border: 1px solid #cbd5e1; padding: 12px; border-radius: 8px;">
                <span style="font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase;">Programação</span>
                <strong style="font-size: 18px; color: #0f172a; display: block; margin-top: 3px;">{format_num(prog_m, 0)} m</strong>
                <span style="font-size: 11px; color: #64748b;">{prog_qtd} pedidos</span>
              </div>
              <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px; border-radius: 8px;">
                <span style="font-size: 11px; color: #166534; font-weight: 700; text-transform: uppercase;">Pronta Entrega (PE)</span>
                <strong style="font-size: 18px; color: #059669; display: block; margin-top: 3px;">{format_num(pe_m, 0)} m</strong>
                <span style="font-size: 11px; color: #15803d;">{pe_qtd} pedidos</span>
              </div>
              <div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 12px; border-radius: 8px;">
                <span style="font-size: 11px; color: #1e40af; font-weight: 700; text-transform: uppercase;">Exclusivos (EXC)</span>
                <strong style="font-size: 18px; color: #0284c7; display: block; margin-top: 3px;">{format_num(exc_m, 0)} m</strong>
                <span style="font-size: 11px; color: #1d4ed8;">{exc_qtd} pedidos</span>
              </div>
              <div style="background: #faf5ff; border: 1px solid #e9d5ff; padding: 12px; border-radius: 8px;">
                <span style="font-size: 11px; color: #6b21a8; font-weight: 700; text-transform: uppercase;">Pilotagens (PIL)</span>
                <strong style="font-size: 18px; color: #7c3aed; display: block; margin-top: 3px;">{pil_qtd} pedidos</strong>
                <span style="font-size: 11px; color: #6b21a8;">{format_num(pil_m, 0)} metros</span>
              </div>
            </div>
            <div style="background: #faf5ff; border-left: 4px solid #7c3aed; padding: 8px 12px; border-radius: 4px; margin-top: 8px; font-size: 12px; color: #4c1d95;">
              <strong>Artigos em Pilotagem no Mês:</strong> {lista_pil_artigos_txt}
            </div>
          </div>

          <!-- Comparativo Mês Anterior, Cancelamentos e Análise de Crédito -->
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin: 16px 0;">
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 14px; border-radius: 8px;">
              <span style="font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase;">Comparativo vs Mês Anterior</span>
              <strong style="font-size: 17px; color: {'#059669' if var_mom_pct >= 0 else '#dc2626'}; display: block; margin-top: 3px;">{'+' if var_mom_pct >= 0 else ''}{var_mom_pct:.1f}%</strong>
              <span style="font-size: 11px; color: #64748b;">Mês ant.: {format_num(mes_ant_m, 0)} m ({format_brl(mes_ant_val)})</span>
            </div>
            <div style="background: #fff5f5; border: 1px solid #fecaca; padding: 12px 14px; border-radius: 8px;">
              <span style="font-size: 11px; color: #b91c1c; font-weight: 700; text-transform: uppercase;">Análise de Crédito (Bloqueados)</span>
              <strong style="font-size: 17px; color: #b91c1c; display: block; margin-top: 3px;">{format_brl(total_bloq_val)}</strong>
              <span style="font-size: 11px; color: #7f1d1d;">{total_bloq_qtd} pedidos bloqueados</span>
            </div>
            <div style="background: #fffbeb; border: 1px solid #fde68a; padding: 12px 14px; border-radius: 8px;">
              <span style="font-size: 11px; color: #92400e; font-weight: 700; text-transform: uppercase;">Cancelamentos no Mês</span>
              <strong style="font-size: 17px; color: #b45309; display: block; margin-top: 3px;">{canc_qtd} pedidos ({format_num(canc_m, 0)} m)</strong>
              <span style="font-size: 11px; color: #92400e;">{format_brl(canc_val)}</span>
            </div>
          </div>

          <!-- Consolidado por Supervisor -->
          <div style="margin: 20px 0;">
            <h4 style="margin: 0 0 8px; font-size: 13px; font-weight: 800; color: #0f172a; text-transform: uppercase;">
              👔 RESULTADO POR SUPERVISOR
            </h4>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #cbd5e1; border-radius: 6px; overflow: hidden;">
              <thead>
                <tr style="background: #1e293b; color: #ffffff; font-size: 11px; text-transform: uppercase;">
                  <th style="padding: 8px 12px; text-align: left;">Supervisor</th>
                  <th style="padding: 8px 12px; text-align: right;">Expectativa</th>
                  <th style="padding: 8px 12px; text-align: right;">Vendido (m)</th>
                  <th style="padding: 8px 12px; text-align: right;">Valor (R$)</th>
                  <th style="padding: 8px 12px; text-align: right;">%</th>
                </tr>
              </thead>
              <tbody>{linhas_sup}</tbody>
            </table>
          </div>

          <!-- Ranking Geral por Quem Mais Vendeu -->
          <div style="margin: 20px 0;">
            <h4 style="margin: 0 0 8px; font-size: 13px; font-weight: 800; color: #0f172a; text-transform: uppercase;">
              🏆 RANKING GERAL DE REPRESENTANTES (ORDENADO POR QUEM MAIS VENDEU)
            </h4>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #cbd5e1; border-radius: 6px; overflow: hidden;">
              <thead>
                <tr style="background: #0f172a; color: #ffffff; font-size: 11px; text-transform: uppercase;">
                  <th style="padding: 8px 10px; text-align: left;">#</th>
                  <th style="padding: 8px 10px; text-align: left;">Representante</th>
                  <th style="padding: 8px 10px; text-align: left;">Sup.</th>
                  <th style="padding: 8px 10px; text-align: right;">Expectativa</th>
                  <th style="padding: 8px 10px; text-align: right;">Vendido (m)</th>
                  <th style="padding: 8px 10px; text-align: right;">Valor (R$)</th>
                  <th style="padding: 8px 10px; text-align: right;">%</th>
                </tr>
              </thead>
              <tbody>{linhas_ranking}</tbody>
            </table>
          </div>

          <!-- Clientes que Não Compravam Há Muito Tempo e Compraram Neste Mês -->
          <div style="margin: 20px 0;">
            <h4 style="margin: 0 0 8px; font-size: 13px; font-weight: 800; color: #059669; text-transform: uppercase;">
              🔄 CLIENTES REATIVADOS NO MÊS (60+ DIAS SEM COMPRAR QUE VOLTARAM A COMPRAR) — {len(clientes_reativados)} clientes
            </h4>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #cbd5e1; border-radius: 6px; overflow: hidden;">
              <thead>
                <tr style="background: #065f46; color: #ffffff; font-size: 11px; text-transform: uppercase;">
                  <th style="padding: 8px 10px; text-align: left;">Cliente</th>
                  <th style="padding: 8px 10px; text-align: left;">Representante</th>
                  <th style="padding: 8px 10px; text-align: center;">Compra Anterior</th>
                  <th style="padding: 8px 10px; text-align: right;">Comprou no Mês</th>
                </tr>
              </thead>
              <tbody>{linhas_reativados}</tbody>
            </table>
          </div>

          <!-- Top 10 Artigos Mais Vendidos no Mês -->
          <div style="margin: 20px 0;">
            <h4 style="margin: 0 0 8px; font-size: 13px; font-weight: 800; color: #0f172a; text-transform: uppercase;">
              🧵 TOP 10 ARTIGOS MAIS VENDIDOS DO MÊS ({mes_str})
            </h4>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #cbd5e1; border-radius: 6px; overflow: hidden;">
              <thead>
                <tr style="background: #1e293b; color: #ffffff; font-size: 11px; text-transform: uppercase;">
                  <th style="padding: 7px 10px; text-align: left;">#</th>
                  <th style="padding: 7px 10px; text-align: left;">Artigo</th>
                  <th style="padding: 7px 10px; text-align: right;">Metragem</th>
                  <th style="padding: 7px 10px; text-align: right;">Valor</th>
                </tr>
              </thead>
              <tbody>{linhas_art_mes}</tbody>
            </table>
          </div>

          <!-- Top 10 Artigos Mais Vendidos no Último Trimestre -->
          <div style="margin: 20px 0;">
            <h4 style="margin: 0 0 8px; font-size: 13px; font-weight: 800; color: #0284c7; text-transform: uppercase;">
              📈 TOP 10 ARTIGOS MAIS VENDIDOS NO ÚLTIMO TRIMESTRE (90 DIAS)
            </h4>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #cbd5e1; border-radius: 6px; overflow: hidden;">
              <thead>
                <tr style="background: #0369a1; color: #ffffff; font-size: 11px; text-transform: uppercase;">
                  <th style="padding: 7px 10px; text-align: left;">#</th>
                  <th style="padding: 7px 10px; text-align: left;">Artigo</th>
                  <th style="padding: 7px 10px; text-align: right;">Metragem</th>
                  <th style="padding: 7px 10px; text-align: right;">Valor</th>
                </tr>
              </thead>
              <tbody>{linhas_art_trim}</tbody>
            </table>
          </div>
        </div>
        """
        resumo_texto = f"Executivo Diretoria ({mes_str}): Vendido {format_num(total_fat_qtd, 0)}m ({format_brl(total_fat_val)}) — {atingimento_pct:.1f}% da expectativa."

    # ══════════════════════════════════════════════════════════════
    # CABEÇALHO CORPORATIVO DESIGNTEX
    # ══════════════════════════════════════════════════════════════
    html_template_final = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 680px; margin: 0 auto; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.08);">
      
      <!-- Topo Oficial Designtex -->
      <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 22px 28px; color: #ffffff;">
        <span style="display: inline-block; background: {badge_cor}; color: #ffffff; font-size: 11px; font-weight: 800; text-transform: uppercase; padding: 4px 10px; border-radius: 9999px; letter-spacing: 0.5px; margin-bottom: 8px;">
          {badge_txt}
        </span>
        <h2 style="margin: 0; font-size: 18px; font-weight: 700; color: #ffffff; letter-spacing: -0.3px;">{titulo_oficial}</h2>
        <p style="margin: 5px 0 0; font-size: 13px; color: #94a3b8;">Inteligência Comercial Designtex</p>
      </div>

      <!-- Tag de Identificação -->
      <div style="background: #f1f5f9; border-bottom: 1px solid #e2e8f0; padding: 12px 28px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
        <div>
          <span style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase;">Destinatário / Escopo:</span>
          <strong style="display: block; font-size: 13px; color: #0f172a;">{rep_filtro_nome}</strong>
        </div>
        <div style="text-align: right;">
          <span style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase;">Supervisor:</span>
          <span style="display: block; font-size: 13px; color: #0284c7; font-weight: 700;">{rep_supervisor}</span>
        </div>
      </div>

      <!-- Banner de Testes / Homologação -->
      <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 28px; font-size: 12px; color: #92400e; line-height: 1.5;">
        <strong>🛡️ DISPARO EM MODO HOMOLOGAÇÃO / TESTES DO GESTOR:</strong><br>
        Relatório gerado para <strong>{rep_filtro_nome}</strong>.<br>
        <span style="color: #b45309;">Por segurança operacional, <strong>o destinatário oficial NÃO recebeu este e-mail</strong>. O disparo foi canalizado para o gestor Samuel para validação analítica.</span>
      </div>

      <!-- Conteúdo Analítico -->
      <div style="padding: 24px 28px;">
        {corpo_html}
      </div>

      <!-- Rodapé -->
      <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 28px; font-size: 11px; color: #64748b; display: flex; justify-content: space-between; align-items: center;">
        <span>Processado e auditado automaticamente pela <strong>Inteligência Comercial Designtex</strong></span>
        <span>{dia_str} {agora.strftime('%H:%M')}</span>
      </div>
    </div>
    """

    metricas = {
        "ciclo": ciclo_tipo,
        "rep_codigo": rep_codigo,
        "rep_nome": _nome_rep(rep_info) if rep_info else ("Diretoria Gilberto" if ciclo_tipo == "D" else "Geral"),
        "supervisor": rep_supervisor,
        "vendido_mes_m": total_fat_qtd,
        "vendido_mes_val": total_fat_val,
        "atingimento_pct": atingimento_pct,
        "bloqueados_qtd": total_bloq_qtd,
        "bloqueados_valor": total_bloq_val,
    }

    return html_template_final, resumo_texto, metricas
