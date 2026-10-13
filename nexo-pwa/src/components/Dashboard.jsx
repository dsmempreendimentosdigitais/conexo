import React, { useId, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
  PieChart,
  Pie,
  Legend,
} from "recharts";

const brl = (v) =>
  Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const meters = (v) =>
  Number(v).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 2 }) + " m";

const COLORS = ["#38bdf8", "#818cf8", "#34d399", "#fb923c", "#f472b6", "#a855f7", "#06b6d4"];

const FABRIC_COLOR_MAP = {
  "natural": "#e5d8c5",
  "cru": "#ede3d2",
  "off white": "#f8fafc",
  "offwhite": "#f8fafc",
  "branco": "#f1f5f9",
  "vanila": "#fef08a",
  "creme": "#fef9c3",
  "bege areia": "#d6c5b3",
  "bege raiz": "#c2b09c",
  "bege": "#d7c4b7",
  "nude rose": "#fbcfe8",
  "nude": "#f3d5d8",
  "rose": "#f472b6",
  "rosa": "#f472b6",
  "verde camelia": "#a7f3d0",
  "verde camélia": "#a7f3d0",
  "verde menta": "#a7f3d0",
  "verde musgo": "#4d7c0f",
  "verde militar": "#3f6212",
  "verde": "#22c55e",
  "azul maya": "#7dd3fc",
  "azul claro": "#bae6fd",
  "azul marinho": "#1e3a8a",
  "marinho": "#1e3a8a",
  "azul": "#38bdf8",
  "preto": "#18181b",
  "black": "#0f172a",
  "amarelo crome": "#facc15",
  "amarelo": "#facc15",
  "vermelho": "#dc2626",
  "vinho": "#881337",
  "bordo": "#780016",
  "bordô": "#780016",
  "caramelo": "#b45309",
  "terra": "#9a3412",
  "cinza": "#64748b",
  "lilas": "#c084fc",
  "lilás": "#c084fc",
  "violeta": "#a855f7",
};

function getHexColor(row, fallbackIndex) {
  if (row && row.hex_color && row.hex_color.startsWith("#")) {
    return row.hex_color;
  }
  const txt = (
    (row.nome_cor || "") + " " +
    (row.cor || "") + " " +
    (row.nome_tecido || "") + " " +
    (row.descricao || "")
  ).toLowerCase();

  for (const [key, hex] of Object.entries(FABRIC_COLOR_MAP)) {
    if (txt.includes(key)) {
      return hex;
    }
  }
  return COLORS[fallbackIndex % COLORS.length];
}

// Helper para formatar o nome completo do rótulo no gráfico
function formatChartLabel(r, defaultKey) {
  const codTecido = r.cod_tecido || r.cod_produto || "";
  const nomeTecido = r.nome_tecido || r.descricao || r.produto || "";
  const codCor = r.cod_cor || r.cor_codigo || "";
  const nomeCor = r.nome_cor || r.cor || "";

  // Se tivermos informações estruturadas de tecido e cor:
  if (nomeTecido || nomeCor) {
    let partTecido = [codTecido, nomeTecido].filter(Boolean).join(" ");
    let partCor = [codCor, nomeCor].filter(Boolean).join(" ");
    if (partTecido && partCor) {
      return `${partTecido} - ${partCor}`;
    }
    return partTecido || partCor;
  }

  return String(r[defaultKey] ?? r.nome ?? "—");
}

// ── KPI simples ──────────────────────────────────────────────
function KpiCards({ dados }) {
  const d = Array.isArray(dados) ? dados[0] : dados;
  if (!d) return null;

  // Suporta tanto conexo_vendas_periodo (faturamento, ticket_medio)
  // quanto conexo_relatorio_periodo (faturado_valor, carteira_valor, faturado_metragem)
  const faturado  = d.faturado_valor  ?? d.faturamento ?? d.total ?? 0;
  const carteira  = d.carteira_valor  ?? null;
  const metragem  = d.faturado_metragem ?? d.metragem ?? null;
  const pedidos   = d.total_pedidos   ?? d.pedidos ?? 0;
  const ticket    = d.ticket_medio    ?? d.ticket ?? (faturado && pedidos ? faturado / pedidos : 0);

  const items = [
    { label: "Faturado",      value: brl(faturado) },
    carteira != null && { label: "Carteira em aberto", value: brl(carteira) },
    metragem != null && { label: "Metros faturados",   value: `${Number(metragem).toLocaleString("pt-BR")} m` },
    !metragem && { label: "Ticket médio",    value: brl(ticket) },
    { label: "Pedidos",       value: Number(pedidos).toLocaleString("pt-BR") },
  ].filter(Boolean);

  return (
    <div className="kpi-grid" style={{ gridTemplateColumns: `repeat(${Math.min(items.length, 3)}, 1fr)` }}>
      {items.map((k) => (
        <div className="kpi-card" key={k.label}>
          <div className="kpi-label">{k.label}</div>
          <div className="kpi-value">{k.value}</div>
        </div>
      ))}
    </div>
  );
}

// ── Gráfico de barras horizontal ────────────────────────────
function Barras({ dados, nameKey, valKey, title }) {
  if (!Array.isArray(dados) || dados.length === 0) return null;

  const isMeter = valKey && (
    valKey.toLowerCase().includes("metr") ||
    valKey.toLowerCase().includes("quantidade") ||
    valKey.toLowerCase().includes("qtd") ||
    valKey.toLowerCase().includes("metros")
  );

  const data = dados.map((r, i) => {
    const valNum = Number(r[valKey] ?? r.faturamento ?? 0);
    const labelTexto = formatChartLabel(r, nameKey);
    return {
      nome: labelTexto.length > 45 ? labelTexto.slice(0, 42) + "..." : labelTexto,
      nomeCompleto: labelTexto,
      valor: valNum,
      valorFmt: isMeter ? meters(valNum) : brl(valNum),
      fill: getHexColor(r, i),
    };
  });

  const total = data.reduce((acc, curr) => acc + curr.valor, 0);

  return (
    <div className="chart-wrapper" style={{ background: "#1e293b", padding: 16, borderRadius: 12, border: "1px solid #334155" }}>
      {title && <div className="chart-title" style={{ color: "#f8fafc", fontSize: 14, fontWeight: 700, marginBottom: 12 }}>{title}</div>}
      <ResponsiveContainer width="100%" height={Math.max(220, data.length * 44)}>
        <BarChart data={data} layout="vertical" margin={{ left: 12, right: 60, top: 8, bottom: 8 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="nome"
            width={240}
            tick={{ fill: "#cbd5e1", fontSize: 11, fontWeight: 500 }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const d = payload[0].payload;
                return (
                  <div style={{ background: "#0f172a", border: "1px solid #38bdf8", borderRadius: 8, padding: "8px 12px", color: "#fff" }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "#94a3b8", marginBottom: 4 }}>{d.nomeCompleto}</div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: isMeter ? "#fb923c" : "#38bdf8" }}>
                      {isMeter ? `Metragem: ${d.valorFmt}` : `Valor: ${d.valorFmt}`}
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="valor" radius={[0, 6, 6, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.fill} stroke="#475569" strokeWidth={1} />
            ))}
            <LabelList dataKey="valorFmt" position="right" fill={isMeter ? "#fb923c" : "#38bdf8"} fontSize={11} fontWeight={700} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div style={{ borderTop: "1px solid #334155", marginTop: 8, paddingTop: 8, color: "#94a3b8", fontSize: 12, textAlign: "right" }}>
        TOTAL: <strong>{isMeter ? meters(total) : brl(total)}</strong>
      </div>
    </div>
  );
}

// ── Gráfico de Pizza / Rosca Inteligente ──────────────────────────
function PizzaChart({ dados, nameKey, valKey, title }) {
  if (!Array.isArray(dados) || dados.length === 0) return null;

  const first = dados[0] || {};
  const hasPcpBreakdown = "quantidade_solicitada" in first || "quantidade_disponivel" in first || "quantidade_reservada" in first;

  let pieData = [];

  if (hasPcpBreakdown) {
    const totalSolicitado = dados.reduce((acc, curr) => acc + (Number(curr.quantidade_solicitada) || 0), 0);
    const totalDisponivel = dados.reduce((acc, curr) => acc + (Number(curr.quantidade_disponivel) || 0), 0);
    const totalReservado  = dados.reduce((acc, curr) => acc + (Number(curr.quantidade_reservada) != null ? Number(curr.quantidade_reservada) : Math.max(0, (Number(curr.quantidade_solicitada) || 0) - (Number(curr.quantidade_disponivel) || 0))), 0);

    const base = totalSolicitado || (totalDisponivel + totalReservado) || 1;
    const pctDisp = ((totalDisponivel / base) * 100).toFixed(1);
    const pctRes  = ((totalReservado / base) * 100).toFixed(1);

    pieData = [
      { name: `Disponível (${pctDisp}%)`, value: totalDisponivel, valueFmt: meters(totalDisponivel), fill: "#10b981", pct: pctDisp },
      { name: `Reservado / Vendido (${pctRes}%)`, value: totalReservado, valueFmt: meters(totalReservado), fill: "#f59e0b", pct: pctRes },
    ].filter(d => d.value > 0);
  } else {
    const isMeter = valKey && (valKey.toLowerCase().includes("metr") || valKey.toLowerCase().includes("quantidade") || valKey.toLowerCase().includes("qtd"));
    const map = {};
    let grandTotal = 0;

    dados.forEach((r, i) => {
      const name = formatChartLabel(r, nameKey || "nome_tecido");
      const val = Number(r[valKey] || r.faturamento || r.valor || r.quantidade_solicitada || 0);
      map[name] = (map[name] || 0) + val;
      grandTotal += val;
    });

    pieData = Object.entries(map).map(([name, val], i) => {
      const pct = grandTotal > 0 ? ((val / grandTotal) * 100).toFixed(1) : "0";
      return {
        name: `${name} (${pct}%)`,
        nomeCompleto: name,
        value: val,
        valueFmt: isMeter ? meters(val) : brl(val),
        fill: getHexColor({ nome_tecido: name }, i),
        pct,
      };
    });
  }

  if (pieData.length === 0) return null;

  return (
    <div className="chart-wrapper" style={{ background: "#1e293b", padding: 16, borderRadius: 12, border: "1px solid #334155", marginTop: 12 }}>
      {title && <div className="chart-title" style={{ color: "#f8fafc", fontSize: 14, fontWeight: 700, marginBottom: 12 }}>{title}</div>}
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={90}
            paddingAngle={3}
            dataKey="value"
          >
            {pieData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} stroke="#0f172a" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const d = payload[0].payload;
                return (
                  <div style={{ background: "#0f172a", border: "1px solid #38bdf8", borderRadius: 8, padding: "8px 12px", color: "#fff" }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "#94a3b8" }}>{d.name}</div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: d.fill, marginTop: 4 }}>
                      Volume: {d.valueFmt} ({d.pct}%)
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            iconType="circle"
            formatter={(val) => <span style={{ color: "#cbd5e1", fontSize: 11, fontWeight: 600 }}>{val}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Comparativo Proporcional MTD (Gráfico de colunas) ───────────
function Comparativo({ dados }) {
  const d = Array.isArray(dados) ? dados[0] : dados;
  if (!d) return null;

  const diaAtual = d.dia_atual || 16;
  
  // Suporta tanto os novos campos MTD quanto os legados
  const atualMtd = Number(d.faturamento_atual_mtd ?? d.faturamento_ref ?? d.faturamento_atual ?? 0);
  const antMtd   = Number(d.faturamento_ant_mtd ?? d.faturamento_ant ?? d.faturamento_anterior ?? 0);
  const anoMtd   = Number(d.faturamento_ano_ant_mtd ?? 0);
  const antFull  = Number(d.faturamento_ant_full ?? 0);

  const data = [
    atualMtd > 0 && { nome: `Set/26 (1-${diaAtual}d MTD)`, valor: atualMtd, valorFmt: brl(atualMtd), fill: "#38bdf8" },
    antMtd > 0 && { nome: `Ago/26 (1-${diaAtual}d MTD)`, valor: antMtd, valorFmt: brl(antMtd), fill: "#818cf8" },
    anoMtd > 0 && { nome: `Set/25 (1-${diaAtual}d MTD)`, valor: anoMtd, valorFmt: brl(anoMtd), fill: "#34d399" },
    antFull > 0 && { nome: `Ago/26 (Mês Cheio)`, valor: antFull, valorFmt: brl(antFull), fill: "#475569" },
  ].filter(Boolean);

  if (data.length === 0) return null;

  return (
    <div className="chart-wrapper" style={{ background: "#1e293b", padding: 16, borderRadius: 12, border: "1px solid #334155", marginTop: 12 }}>
      <div className="chart-title" style={{ color: "#f8fafc", fontSize: 14, fontWeight: 700, marginBottom: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span>📊 Comparativo Proporcional MTD (1 ao dia {diaAtual})</span>
        <span style={{ fontSize: 11, color: "#38bdf8", fontWeight: 600 }}>Projeção 30d: {brl(d.projecao_fechamento_mes || 0)}</span>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 20, right: 20, left: 10, bottom: 20 }}>
          <XAxis dataKey="nome" tick={{ fill: "#cbd5e1", fontSize: 11, fontWeight: 600 }} />
          <YAxis hide />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload;
                return (
                  <div style={{ background: "#0f172a", border: "1px solid #38bdf8", borderRadius: 8, padding: "8px 12px", color: "#fff" }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "#94a3b8", marginBottom: 4 }}>{item.nome}</div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: item.fill }}>Faturamento: {item.valorFmt}</div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="valor" radius={[6, 6, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} stroke="#334155" strokeWidth={1} />
            ))}
            <LabelList dataKey="valorFmt" position="top" fill="#f8fafc" fontSize={11} fontWeight={700} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Tabela analítica com linhas e colunas */}
      <div style={{ marginTop: 12, borderTop: "1px solid #334155", paddingTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, color: "#cbd5e1" }}>
          <thead>
            <tr style={{ background: "#0f172a" }}>
              <th style={{ padding: "6px 8px", textAlign: "left", color: "#94a3b8" }}>PERÍODO MTD</th>
              <th style={{ padding: "6px 8px", textAlign: "right", color: "#94a3b8" }}>FATURAMENTO</th>
              <th style={{ padding: "6px 8px", textAlign: "right", color: "#94a3b8" }}>METRAGEM</th>
              <th style={{ padding: "6px 8px", textAlign: "right", color: "#94a3b8" }}>VARIAÇÃO MTD</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ background: "transparent" }}>
              <td style={{ padding: "6px 8px", fontWeight: 700, color: "#38bdf8" }}>Set/26 (1-{diaAtual}d MTD)</td>
              <td style={{ padding: "6px 8px", textAlign: "right", fontWeight: 700, color: "#f8fafc" }}>{brl(atualMtd)}</td>
              <td style={{ padding: "6px 8px", textAlign: "right", color: "#fb923c" }}>{meters(d.metragem_atual_mtd || 0)}</td>
              <td style={{ padding: "6px 8px", textAlign: "right", fontWeight: 700, color: "#38bdf8" }}>Atual</td>
            </tr>
            {antMtd > 0 && (
              <tr style={{ background: "#0f172a" }}>
                <td style={{ padding: "6px 8px", fontWeight: 600, color: "#818cf8" }}>Ago/26 (1-{diaAtual}d MTD)</td>
                <td style={{ padding: "6px 8px", textAlign: "right", fontWeight: 600, color: "#f8fafc" }}>{brl(antMtd)}</td>
                <td style={{ padding: "6px 8px", textAlign: "right", color: "#fb923c" }}>{meters(d.metragem_ant_mtd || 0)}</td>
                <td style={{ padding: "6px 8px", textAlign: "right", fontWeight: 700, color: (atualMtd - antMtd) >= 0 ? "#22c55e" : "#ef4444" }}>
                  {((atualMtd - antMtd) / antMtd * 100).toFixed(2)}%
                </td>
              </tr>
            )}
            {anoMtd > 0 && (
              <tr style={{ background: "transparent" }}>
                <td style={{ padding: "6px 8px", fontWeight: 600, color: "#34d399" }}>Set/25 (1-{diaAtual}d MTD)</td>
                <td style={{ padding: "6px 8px", textAlign: "right", fontWeight: 600, color: "#f8fafc" }}>{brl(anoMtd)}</td>
                <td style={{ padding: "6px 8px", textAlign: "right", color: "#fb923c" }}>{meters(d.metragem_ano_ant_mtd || 0)}</td>
                <td style={{ padding: "6px 8px", textAlign: "right", fontWeight: 700, color: (atualMtd - anoMtd) >= 0 ? "#22c55e" : "#ef4444" }}>
                  {((atualMtd - anoMtd) / anoMtd * 100).toFixed(2)}%
                </td>
              </tr>
            )}
            {antFull > 0 && (
              <tr style={{ background: "#0f172a" }}>
                <td style={{ padding: "6px 8px", color: "#94a3b8" }}>Ago/26 (Mês Cheio)</td>
                <td style={{ padding: "6px 8px", textAlign: "right", color: "#94a3b8" }}>{brl(antFull)}</td>
                <td style={{ padding: "6px 8px", textAlign: "right", color: "#94a3b8" }}>{meters(d.metragem_ant_full || 0)}</td>
                <td style={{ padding: "6px 8px", textAlign: "right", color: "#94a3b8" }}>Mês Cheio</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Fontes de mercado ───────────────────────────────────────
function Fontes({ fontes }) {
  if (!fontes || fontes.length === 0) return null;
  return (
    <div className="sources">
      <div className="sources-title">Fontes consultadas</div>
      {fontes.map((f, i) => (
        <a key={i} href={f.fonte} target="_blank" rel="noreferrer" className="source-link">
          🔗 {f.titulo}{f.data ? ` (${f.data.slice(0, 10)})` : ""}
        </a>
      ))}
    </div>
  );
}

// Função utilitária universal de visualização/download de PDF compatível com Celulares (iOS Safari / Android) e PCs
function abrirImpressaoUniversal(htmlContent, titulo = "Relatório CONEXO") {
  const dataHoje = new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" });
  
  // Higieniza HTML limpando cores claras de modo escuro para garantir texto 100% PRETO e alto contraste no PDF
  const cleanedHtml = (htmlContent || "")
    .replace(/color:\s*(#f8fafc|#cbd5e1|#94a3b8|#64748b|rgb\(248,\s*250,\s*252\)|rgb\(203,\s*213,\s*225\)|rgb\(148,\s*163,\s*184\)|rgb\(100,\s*116,\s*139\)|inherit)/gi, "color: #000000")
    .replace(/background:\s*(#1e293b|rgb\(30,\s*41,\s*59\))/gi, "background: transparent")
    .replace(/border-bottom:\s*1px\s*solid\s*(#1e293b|#334155|rgb\(30,\s*41,\s*59\)|rgb\(51,\s*65,\s*85\))/gi, "border-bottom: 1px solid #cbd5e1");

  const fullHtml = `<!DOCTYPE html><html lang="pt-BR"><head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
    <title>${titulo} — ${dataHoje}</title>
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; color: #000000; background: #f8fafc; padding: 16px; font-size: 12px; margin: 0; }
      .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; background: #0f172a; color: white; padding: 12px 16px; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); gap: 12px; flex-wrap: wrap; }
      .header-left { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
      .btn-voltar { background: #1e293b; color: #ffffff; border: 1px solid #475569; padding: 10px 18px; border-radius: 8px; font-weight: 700; font-size: 13px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); text-decoration: none; transition: background 0.2s; }
      .btn-voltar:hover, .btn-voltar:active { background: #334155; border-color: #94a3b8; }
      .btn-print { background: #0284c7; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 700; font-size: 13px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
      .btn-print:hover { background: #0369a1; }
      .bottom-bar { display: flex; gap: 12px; margin-top: 20px; padding: 14px 16px; background: #0f172a; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); flex-wrap: wrap; }
      .report-card { background: #ffffff; padding: 24px; border-radius: 12px; border: 1px solid #cbd5e1; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
      
      /* Regra estrita: Toda a tipografia de dados no relatório é PRETA (#000000) para máxima visibilidade e contraste */
      .report-card, 
      .report-card table, 
      .report-card tbody, 
      .report-card tr, 
      .report-card td, 
      .report-card p, 
      .report-card span, 
      .report-card div:not(.no-print) {
        color: #000000 !important;
      }
      .report-card h1 { font-size: 20px; font-weight: 800; color: #000000 !important; margin: 0 0 6px 0; }
      .report-card .subtitulo { color: #334155 !important; font-size: 12px; font-weight: 600; margin-bottom: 20px; }
      .report-card .section-title, .report-card .chart-title { font-size: 14px !important; font-weight: 800 !important; color: #000000 !important; margin: 20px 0 10px !important; border-bottom: 2px solid #000000 !important; padding-bottom: 6px !important; text-transform: uppercase !important; }
      .report-card table { width: 100% !important; border-collapse: collapse !important; margin-bottom: 20px !important; font-size: 12px !important; }
      .report-card th { text-align: left !important; padding: 8px 8px !important; background: #0f172a !important; color: #ffffff !important; font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase !important; border-bottom: 2px solid #000000 !important; }
      .report-card td { padding: 8px 8px !important; border-bottom: 1px solid #cbd5e1 !important; color: #000000 !important; font-size: 12px !important; font-weight: 600 !important; }
      .report-card tr:nth-child(even) td { background: #f8fafc !important; }
      .report-card tr:nth-child(odd) td { background: #ffffff !important; }
      .report-card tfoot tr td { background: #0f172a !important; color: #ffffff !important; font-weight: 700 !important; }
      .report-card .footer { margin-top: 28px !important; font-size: 11px !important; color: #475569 !important; border-top: 1px solid #cbd5e1 !important; padding-top: 10px !important; font-weight: 500 !important; }
      
      .kpi-grid { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
      .kpi-card { border: 1px solid #cbd5e1; padding: 10px 14px; border-radius: 8px; min-width: 110px; flex: 1; background: #f8fafc; }
      .kpi-label { font-size: 10px; color: #64748b; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 2px; }
      .kpi-value { font-size: 18px; font-weight: 700; color: #0f172a; }
      
      @media print {
        .no-print { display: none !important; }
        body { padding: 0; background: white; }
        .report-card { border: none; box-shadow: none; padding: 0; }
      }
    </style>
  </head><body>
    <div class="header-bar no-print">
      <div class="header-left">
        <button class="btn-voltar" onclick="voltarAoConexo()">⬅️ Voltar ao CONEXO</button>
        <div>
          <div style="font-size:14px; font-weight:700;">📄 Relatório Comercial CONEXO</div>
          <div style="font-size:11px; opacity:0.85;">Visualização de Relatório</div>
        </div>
      </div>
      <button class="btn-print" onclick="window.print()">🖨️ Salvar em PDF</button>
    </div>
    <div class="report-card">
      <h1>📊 ${titulo}</h1>
      <div class="subtitulo">Gerado em ${dataHoje} — Designtex Tecidos / CONEXO</div>
      ${cleanedHtml}
      <div class="footer">Gerado automaticamente pelo CONEXO — Inteligência Comercial</div>
    </div>
    <div class="bottom-bar no-print">
      <button class="btn-voltar" onclick="voltarAoConexo()" style="flex:1; justify-content:center;">⬅️ Voltar ao CONEXO</button>
      <button class="btn-print" onclick="window.print()" style="flex:1; justify-content:center;">🖨️ Salvar em PDF</button>
    </div>
    <script>
      function voltarAoConexo() {
        try {
          if (window.opener && !window.opener.closed) {
            window.close();
            return;
          }
        } catch(e) {}
        try {
          window.close();
        } catch(e) {}
        if (window.history && window.history.length > 1) {
          window.history.back();
        } else {
          window.location.href = window.location.origin || "/";
        }
      }

      // No desktop dispara a caixa de impressão automaticamente
      if (!/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
        setTimeout(function() { window.print(); }, 400);
      }
    </script>
  </body></html>`;

  const win = window.open("", "_blank");
  if (win) {
    win.document.open();
    win.document.write(fullHtml);
    win.document.close();
  } else {
    // Fallback se houver bloqueador de popup no celular
    const winLocation = window.open();
    if (winLocation) {
      winLocation.document.open();
      winLocation.document.write(fullHtml);
      winLocation.document.close();
    }
  }
}

// Wrapper visual com botões de PDF (Relatório Completo e Apenas Gráficos)
function PdfWrapper({ children, title = "Relatório CONEXO" }) {
  const rawId = useId ? useId() : `pdf-${Math.random().toString(36).substring(2, 9)}`;
  const containerId = String(rawId).replace(/:/g, "");
  const [modalData, setModalData] = useState(null);

  function abrirModalPDF(apenasGraficos = false) {
    const container = document.getElementById(containerId);
    if (!container) return;

    let htmlLimpo = "";
    if (apenasGraficos) {
      const clone = container.cloneNode(true);
      const tabelas = clone.querySelectorAll(".pdf-tabela");
      tabelas.forEach(t => t.remove());
      htmlLimpo = clone.innerHTML;
    } else {
      htmlLimpo = container.innerHTML;
    }

    // Higieniza garantindo texto 100% preto
    htmlLimpo = (htmlLimpo || "")
      .replace(/color:\s*(#f8fafc|#cbd5e1|#94a3b8|#64748b|rgb\(248,\s*250,\s*252\)|rgb\(203,\s*213,\s*225\)|rgb\(148,\s*163,\s*184\)|rgb\(100,\s*116,\s*139\)|inherit)/gi, "color: #000000")
      .replace(/background:\s*(#1e293b|rgb\(30,\s*41,\s*59\))/gi, "background: transparent")
      .replace(/border-bottom:\s*1px\s*solid\s*(#1e293b|#334155|rgb\(30,\s*41,\s*59\)|rgb\(51,\s*65,\s*85\))/gi, "border-bottom: 1px solid #cbd5e1");

    setModalData({
      titulo: apenasGraficos ? `Gráficos — ${title}` : title,
      html: htmlLimpo,
      dataHoje: new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" }),
    });
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 12 }}>
      <div className="no-print" style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button
          onClick={() => abrirModalPDF(false)}
          style={{
            background: "#38bdf8",
            color: "#0f172a",
            border: "none",
            borderRadius: 8,
            padding: "8px 16px",
            fontWeight: 700,
            fontSize: 13,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: 6,
            boxShadow: "0 2px 8px rgba(56, 189, 248, 0.25)"
          }}
        >
          📄 Baixar Relatório Completo (PDF)
        </button>
        <button
          onClick={() => abrirModalPDF(true)}
          style={{
            background: "#10b981",
            color: "#0f172a",
            border: "none",
            borderRadius: 8,
            padding: "8px 16px",
            fontWeight: 700,
            fontSize: 13,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: 6,
            boxShadow: "0 2px 8px rgba(16, 185, 129, 0.25)"
          }}
        >
          📊 Baixar Apenas Gráficos (PDF)
        </button>
      </div>

      <div id={containerId}>
        {children}
      </div>

      {/* MODAL IN-APP DE VISUALIZAÇÃO E DOWNLOAD DE PDF COM BOTÃO FECHAR 100% GARANTIDO */}
      {modalData && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            width: "100vw",
            height: "100vh",
            backgroundColor: "#f1f5f9",
            zIndex: 999999,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          {/* Top Bar com botão Voltar proeminente */}
          <div
            className="no-print"
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "12px 16px",
              background: "#0f172a",
              color: "#ffffff",
              boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
              gap: 12,
              flexShrink: 0,
              zIndex: 10,
            }}
          >
            <button
              onClick={() => setModalData(null)}
              style={{
                background: "#0284c7",
                color: "#ffffff",
                border: "none",
                padding: "10px 18px",
                borderRadius: 8,
                fontWeight: 800,
                fontSize: 14,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
                boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
              }}
            >
              ⬅️ Voltar ao CONEXO
            </button>

            <span
              style={{
                fontSize: 14,
                fontWeight: 700,
                color: "#f8fafc",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                flex: 1,
                textAlign: "center",
              }}
            >
              📄 {modalData.titulo}
            </span>

            <div style={{ display: "flex", gap: 8 }}>
              <button
                onClick={() => window.print()}
                style={{
                  background: "#10b981",
                  color: "#0f172a",
                  border: "none",
                  padding: "10px 16px",
                  borderRadius: 8,
                  fontWeight: 800,
                  fontSize: 13,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                🖨️ Salvar em PDF
              </button>
              <button
                onClick={() => setModalData(null)}
                style={{
                  background: "#334155",
                  color: "#ffffff",
                  border: "none",
                  padding: "10px 14px",
                  borderRadius: 8,
                  fontWeight: 700,
                  fontSize: 13,
                  cursor: "pointer",
                }}
                title="Fechar"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Área do Relatório Rolável com Alta Legibilidade */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "16px",
              display: "flex",
              justifyContent: "center",
            }}
          >
            <div
              className="report-card"
              style={{
                width: "100%",
                maxWidth: "850px",
                backgroundColor: "#ffffff",
                padding: "24px",
                borderRadius: "12px",
                border: "1px solid #cbd5e1",
                boxShadow: "0 4px 15px rgba(0,0,0,0.06)",
                color: "#000000",
                height: "fit-content",
                marginBottom: "40px",
              }}
            >
              <h1 style={{ fontSize: 22, fontWeight: 800, color: "#000000", margin: "0 0 6px 0" }}>
                📊 {modalData.titulo}
              </h1>
              <div style={{ fontSize: 12, fontWeight: 600, color: "#475569", marginBottom: 20 }}>
                Gerado em {modalData.dataHoje} — Designtex Tecidos / CONEXO
              </div>

              <div
                style={{ color: "#000000" }}
                dangerouslySetInnerHTML={{ __html: modalData.html }}
              />

              <div
                style={{
                  marginTop: 28,
                  paddingTop: 12,
                  borderTop: "1px solid #cbd5e1",
                  fontSize: 11,
                  color: "#64748b",
                  fontWeight: 500,
                }}
              >
                Gerado automaticamente pelo CONEXO — Inteligência Comercial
              </div>

              {/* Botões de Rodapé na Visualização Mobile */}
              <div
                className="no-print"
                style={{
                  display: "flex",
                  gap: 12,
                  marginTop: 28,
                  paddingTop: 16,
                  borderTop: "2px solid #e2e8f0",
                }}
              >
                <button
                  onClick={() => setModalData(null)}
                  style={{
                    flex: 1,
                    background: "#0284c7",
                    color: "#ffffff",
                    border: "none",
                    padding: "14px",
                    borderRadius: 8,
                    fontWeight: 800,
                    fontSize: 14,
                    cursor: "pointer",
                    boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
                  }}
                >
                  ⬅️ Voltar ao CONEXO
                </button>
                <button
                  onClick={() => window.print()}
                  style={{
                    flex: 1,
                    background: "#10b981",
                    color: "#0f172a",
                    border: "none",
                    padding: "14px",
                    borderRadius: 8,
                    fontWeight: 800,
                    fontSize: 14,
                    cursor: "pointer",
                  }}
                >
                  🖨️ Salvar em PDF
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Wrapper de gráfico que oculta da tela por padrão (a menos que a pergunta peça por gráfico ou seja exportação de PDF)
// Wrapper de gráfico inteligente que exibe gráficos proativamente em comparações, rankings e análises
function SmartChartBlock({ children, pergunta = "", forceVisible = true }) {
  const p = (pergunta || "").toLowerCase();

  // Exibe gráficos proativamente se forceVisible for true (padrão) ou se a pergunta sugerir análise visual
  const exibeGrafico = forceVisible || (
    p.includes("grafico") ||
    p.includes("gráfico") ||
    p.includes("barras") ||
    p.includes("colunas") ||
    p.includes("comparar") ||
    p.includes("comparativo") ||
    p.includes("vs") ||
    p.includes("ranking") ||
    p.includes("top") ||
    p.includes("visualizacao")
  );

  if (exibeGrafico) {
    return <div className="chart-block">{children}</div>;
  }

  return (
    <div className="pdf-only-chart" style={{ display: "none" }}>
      {children}
    </div>
  );
}

// ── Roteador principal de dashboards ───────────────────────
export default function Dashboard({ intent, dados, pergunta = "" }) {
  if (!dados) return null;

  // Normaliza dados para sempre ser um array legível de objetos
  const listaDados = Array.isArray(dados)
    ? dados
    : typeof dados === "object"
    ? [dados]
    : [];

  const cleanIntent = intent ? String(intent).replace("conexo_", "nexo_") : "";

  let content = null;
  let title = "Relatório CONEXO";

  switch (cleanIntent) {
    case "nexo_vendas_periodo":
      content = <KpiCards dados={dados} />;
      title = "Resumo de Vendas";
      break;

    case "nexo_comparativo_mes":
    case "nexo_comparativo_ano":
      content = <Comparativo dados={dados} />;
      title = "Comparativo de Vendas";
      break;

    case "nexo_ranking_vendedores":
      content = (
        <div>
          <TabelaSimples dados={listaDados} titulo="Ranking de Vendedores" />
          <SmartChartBlock pergunta={pergunta}>
            <BarrasIntent dados={listaDados} nameKey="vendedor" valKey="faturamento" title="Ranking de Vendedores" />
          </SmartChartBlock>
        </div>
      );
      title = "Ranking de Vendedores";
      break;

    case "nexo_top_clientes":
      content = (
        <div>
          <TabelaSimples dados={listaDados} titulo="Top Clientes" />
          <SmartChartBlock pergunta={pergunta}>
            <BarrasIntent dados={listaDados} nameKey="cliente" valKey="faturamento" title="Top Clientes" />
          </SmartChartBlock>
        </div>
      );
      title = "Top Clientes";
      break;

    case "nexo_top_produtos":
      content = (
        <div>
          <TabelaSimples dados={listaDados} titulo="Top Produtos" />
          <SmartChartBlock pergunta={pergunta}>
            <BarrasIntent dados={listaDados} nameKey="produto" valKey="faturamento" title="Top Produtos" />
          </SmartChartBlock>
        </div>
      );
      title = "Top Produtos";
      break;

    case "nexo_vendas_regiao":
      content = (
        <div>
          <TabelaSimples dados={listaDados} titulo="Vendas por Estado" />
          <SmartChartBlock pergunta={pergunta}>
            <BarrasIntent dados={listaDados} nameKey="uf" valKey="faturamento" title="Vendas por Estado" />
          </SmartChartBlock>
        </div>
      );
      title = "Vendas por Estado";
      break;

    case "nexo_consulta_estoque": {
      if (listaDados.length === 0) return null;
      const sample = listaDados[0] || {};
      const nameKey = sample.cor ? "cor" : sample.descricao ? "descricao" : "cod_produto";
      content = (
        <div>
          <TabelaSimples dados={listaDados} titulo="Disponibilidade de Estoque (Pronto-Entrega)" />
          <SmartChartBlock pergunta={pergunta}>
            <BarrasIntent dados={listaDados} nameKey={nameKey} valKey="quantidade_disponivel" title="Metros Disponíveis em Estoque" />
          </SmartChartBlock>
        </div>
      );
      title = "Relatório de Estoque";
      break;
    }

    case "nexo_consulta_programacao": {
      if (listaDados.length === 0) return null;
      const sample = listaDados[0] || {};
      const nameKey = sample.nome_tecido ? "nome_tecido" : sample.nome_cor ? "nome_cor" : "op";
      content = (
        <div>
          <TabelaSimples dados={listaDados} titulo="Programação de Produção (PCP)" />
          <SmartChartBlock pergunta={pergunta}>
            <PizzaChart dados={listaDados} nameKey={nameKey} valKey="quantidade_solicitada" title="Proporção & Análise da Produção (PCP)" />
          </SmartChartBlock>
        </div>
      );
      title = "Programação de Produção PCP";
      break;
    }

    case "nexo_relatorio_periodo":
      return <RelatorioCompleto dados={dados} />;

    case "nexo_consulta_geral": {
      if (listaDados.length === 0) return null;
      const firstRow = listaDados[0];
      const keys = Object.keys(firstRow);
      
      const p = (pergunta || "").toLowerCase();
      const hasOpOrPcp = "op" in firstRow || "quantidade_solicitada" in firstRow || "quantidade_reservada" in firstRow || p.includes("op") || p.includes("pcp") || p.includes("programacao") || p.includes("proporcao") || p.includes("pizza") || p.includes("artigo");

      const numericCandidates = ["quantidade_disponivel", "quantidade_solicitada", "quantidade_reservada", "valor_nf", "valor_total", "faturamento", "valor", "total", "metros", "quantidade", "quantidade_total"];
      let valKey = keys.find(k => numericCandidates.includes(k.toLowerCase()));
      if (!valKey) {
        valKey = keys.find(k => typeof firstRow[k] === "number");
      }
      
      const textCandidates = ["nome_tecido", "descricao", "nome_cor", "cor", "totvs_order_code", "cliente_nome", "cliente", "representante_nome", "vendedor", "nome", "uf", "produto", "artigo", "op"];
      let nameKey = keys.find(k => textCandidates.includes(k.toLowerCase()));
      if (!nameKey) {
        nameKey = keys.find(k => typeof firstRow[k] === "string" && !k.toLowerCase().includes("data") && !k.toLowerCase().includes("created"));
      }
      
      content = (
        <div>
          <TabelaSimples dados={listaDados} titulo="Dados Consultados" />
          {valKey && nameKey && (
            <SmartChartBlock pergunta={pergunta}>
              {hasOpOrPcp ? (
                <PizzaChart dados={listaDados} nameKey={nameKey} valKey={valKey} title="Proporção & Análise de Volume (PCP / Produção)" />
              ) : (
                <BarrasIntent dados={listaDados} nameKey={nameKey} valKey={valKey} title="Visualização Gráfica" />
              )}
            </SmartChartBlock>
          )}
        </div>
      );
      title = "Consulta Comercial CONEXO";
      break;
    }

    case "nexo_inteligencia_mercado":
      content = typeof dados === "object" && dados.fontes ? <Fontes fontes={dados.fontes} /> : null;
      title = "Inteligência de Mercado";
      break;

    default:
      if (listaDados.length > 0) {
        content = <TabelaSimples dados={listaDados} titulo="Resultados da Consulta" />;
        title = "Relatório CONEXO";
      } else {
        return null;
      }
  }

  if (!content) return null;
  return <PdfWrapper title={title}>{content}</PdfWrapper>;
}

// Helper para evitar duplicação
function BarrasIntent({ dados, nameKey, valKey, title }) {
  const lista = Array.isArray(dados) ? dados : [];
  return <Barras dados={lista} nameKey={nameKey} valKey={valKey} title={title} />;
}

// Componente de quadradinho da cor exata
function ColorSquare({ colorHex }) {
  if (!colorHex) return null;
  return (
    <span
      style={{
        display: "inline-block",
        width: 14,
        height: 14,
        backgroundColor: colorHex,
        borderRadius: 3,
        border: "1px solid #94a3b8",
        marginRight: 6,
        verticalAlign: "middle",
        boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
      }}
    />
  );
}

// Tabela simples para exibir lista de linhas no relatório PDF
function TabelaSimples({ dados, titulo }) {
  if (!Array.isArray(dados) || dados.length === 0) return null;
  
  const rawColunas = Object.keys(dados[0]);

  // Remove a coluna duplicada 'valor_total_geral' e 'metragem_total_geral' da exibição da tabela
  const colunas = rawColunas.filter((col) => {
    const c = col.toLowerCase();
    if (
      c === "valor_total_geral" ||
      c === "metragem_total_geral" ||
      c.includes("valor_total_dos_pedidos_geral") ||
      c.includes("metragem_total_dos_pedidos_geral")
    ) {
      return false;
    }
    return true;
  });

  // Função estrita para determinar se a coluna é somável (Valores ou Metragens, NUNCA códigos/IDs)
  const isSummableColumn = (col) => {
    const c = col.toLowerCase();
    if (c.includes("total_pedidos") || c.includes("cod") || c.includes("code") || c.includes("id") || c.includes("op") || c.includes("pedido") || c.includes("order") || c.includes("cpf") || c.includes("cnpj")) {
      return false;
    }
    return (
      c.includes("valor") ||
      c.includes("faturamento") ||
      c.includes("metr") ||
      c.includes("quantidade") ||
      c.includes("qtd") ||
      c.includes("receita") ||
      c.includes("ticket")
    );
  };

  // Calcula totais apenas das colunas somáveis
  const totais = {};
  colunas.forEach((col) => {
    if (isSummableColumn(col)) {
      const soma = dados.reduce((acc, curr) => acc + (Number(curr[col]) || 0), 0);
      totais[col] = soma;
    }
  });

  const fmt = (v, col) => {
    if (v == null || v === "") return "—";
    const colLower = (col || "").toLowerCase();
    
    // Formata qualquer data ISO (AAAA-MM-DD ou AAAA-MM-DDTHH:mm:ss) para o padrão brasileiro DD/MM/AAAA
    if (typeof v === "string") {
      const dateMatch = v.match(/^(\d{4})-(\d{2})-(\d{2})/);
      if (dateMatch) {
        const [, ano, mes, dia] = dateMatch;
        return `${dia}/${mes}/${ano}`;
      }
    }

    // Se for código ou ID, retorna como texto puro sem formatação de moeda
    if (colLower.includes("cod") || colLower.includes("code") || colLower.includes("id") || colLower.includes("op") || colLower.includes("pedido") || colLower.includes("numero")) {
      return String(v);
    }

    if (typeof v === "number" || (!isNaN(Number(v)) && typeof v !== "string")) {
      const num = Number(v);
      const isMeter = (
        colLower.includes("metr") ||
        colLower.includes("quantidade") ||
        colLower.includes("qtd") ||
        colLower.includes("metros")
      );
      const isMoney = (
        colLower.includes("valor") ||
        colLower.includes("faturamento") ||
        colLower.includes("receita") ||
        colLower.includes("previsao_faturamento")
      );
      if (isMeter) return meters(num);
      if (isMoney) return brl(num);
      return num.toLocaleString("pt-BR");
    }
    return String(v);
  };

  const isIndexCol = (c) => {
    const cLower = c.toLowerCase();
    return cLower.includes("total_pedidos") || cLower.includes("total_itens") || cLower === "index" || cLower === "nº";
  };

  return (
    <div className="pdf-tabela" style={{ marginTop: 8 }}>
      {titulo && <div className="chart-title" style={{ fontSize: 13, fontWeight: 700, color: "#f8fafc", marginBottom: 6 }}>{titulo}</div>}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, color: "#cbd5e1" }}>
        <thead>
          <tr>
            {colunas.map((c) => (
              <th key={c} style={{ textAlign: isIndexCol(c) ? "center" : "left", padding: "6px 8px", borderBottom: "1px solid #334155", color: "#94a3b8", fontWeight: 600, background: "#0f172a" }}>
                {isIndexCol(c) ? "Nº" : c.replace(/_/g, " ").toUpperCase()}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dados.slice(0, 50).map((row, i) => {
            const rowHex = getHexColor(row, i);
            return (
              <tr key={i} style={{ background: i % 2 === 0 ? "transparent" : "#1e293b" }}>
                {colunas.map((c) => {
                  const cLower = c.toLowerCase();
                  const isColorCol = cLower.includes("cor") || cLower.includes("color") || cLower === "hex_color";

                  return (
                    <td key={c} style={{ padding: "5px 8px", borderBottom: "1px solid #1e293b", textAlign: isIndexCol(c) ? "center" : "left", fontWeight: isIndexCol(c) ? 700 : 400, color: isIndexCol(c) ? "#38bdf8" : "inherit" }}>
                      {isColorCol && <ColorSquare colorHex={rowHex} />}
                      {isIndexCol(c) ? i + 1 : cLower === "hex_color" ? rowHex : fmt(row[c], c)}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr style={{ background: "#0f172a", borderTop: "2px solid #38bdf8", fontWeight: 700, color: "#f8fafc" }}>
            {colunas.map((c, i) => {
              let footerVal = "";
              if (isIndexCol(c)) {
                footerVal = String(dados[0][c] || dados.length);
              } else if (i === 0 && !colunas.some(isIndexCol)) {
                footerVal = "TOTAL GERAL";
              } else if (totais[c] !== undefined) {
                footerVal = fmt(totais[c], c);
              }
              return (
                <td key={c} style={{ padding: "8px", borderBottom: "1px solid #38bdf8", textAlign: isIndexCol(c) ? "center" : "left", color: isIndexCol(c) ? "#38bdf8" : "#f8fafc" }}>
                  {footerVal}
                </td>
              );
            })}
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

// Relatório consolidado — múltiplos blocos com botão de PDF
function RelatorioCompleto({ dados }) {
  if (!dados || typeof dados !== "object") return null;

  return (
    <PdfWrapper title="Relatório Consolidado de Período">
      {dados.resumo && <KpiCards dados={dados.resumo} />}
      {dados.top_clientes      && <TabelaSimples dados={dados.top_clientes}      titulo="Top Clientes" />}
      {dados.top_produtos      && <TabelaSimples dados={dados.top_produtos}      titulo="Top Produtos" />}
      {dados.ranking_vendedores && <TabelaSimples dados={dados.ranking_vendedores} titulo="Ranking Vendedores" />}
      {dados.por_regiao        && <TabelaSimples dados={dados.por_regiao}        titulo="Por Estado (UF)" />}
      {/* Gráficos visuais abaixo das tabelas */}
      {dados.top_clientes      && <Barras dados={dados.top_clientes}      nameKey="cliente"  valKey="faturamento" title="Top clientes"    />}
      {dados.top_produtos      && <Barras dados={dados.top_produtos}      nameKey="produto"  valKey="faturamento" title="Top produtos"    />}
      {dados.ranking_vendedores && <Barras dados={dados.ranking_vendedores} nameKey="vendedor" valKey="faturamento" title="Ranking vendedores" />}
      {dados.por_regiao        && <Barras dados={dados.por_regiao}        nameKey="uf"       valKey="faturamento" title="Por estado"      />}
    </PdfWrapper>
  );
}

