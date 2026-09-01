import React, { useId } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
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

// ── Comparativo (2 barras: atual vs anterior) ───────────────
function Comparativo({ dados }) {
  const d = Array.isArray(dados) ? dados[0] : dados;
  if (!d) return null;

  const atual    = Number(d.faturamento_ref ?? d.faturamento_atual ?? 0);
  const anterior = Number(d.faturamento_ant ?? d.faturamento_anterior ?? 0);
  const label1   = d.mes_ref ? `${d.mes_ref}` : "Atual";
  const label2   = "Anterior";

  const data = [
    { nome: label1, valor: atual,    fill: "#38bdf8" },
    { nome: label2, valor: anterior, fill: "#475569" },
  ];

  return (
    <div className="chart-wrapper">
      <div className="chart-title">Comparativo de faturamento</div>
      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={data} margin={{ left: 8, right: 16 }}>
          <XAxis dataKey="nome" tick={{ fill: "#94a3b8", fontSize: 12 }} />
          <YAxis hide />
          <Tooltip formatter={(v) => brl(v)} contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }} />
          <Bar dataKey="valor" radius={[6, 6, 0, 0]}>
            {data.map((d, i) => <Cell key={i} fill={d.fill} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
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

// Função utilitária universal de download/impressão de PDF
function baixarPDFUniversal(elementId, titulo = "Relatório CONEXO") {
  const conteudo = document.getElementById(elementId);
  if (!conteudo) return;

  const dataHoje = new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" });

  const anterior = document.getElementById("conexo-print-frame");
  if (anterior) anterior.remove();

  const iframe = document.createElement("iframe");
  iframe.id = "conexo-print-frame";
  iframe.style.cssText = "position:fixed;top:-9999px;left:-9999px;width:900px;height:1px;border:none;visibility:hidden;";
  document.body.appendChild(iframe);

  const doc = iframe.contentDocument || iframe.contentWindow.document;
  doc.open();
  doc.write(`<!DOCTYPE html><html lang="pt-BR"><head>
    <meta charset="UTF-8"/>
    <title>${titulo} — ${dataHoje}</title>
    <style>
      body { font-family: Arial, sans-serif; color: #1a1a2e; background: white; padding: 24px; font-size: 13px; }
      h1 { font-size: 20px; color: #0f172a; margin-bottom: 4px; }
      .subtitulo { color: #64748b; font-size: 12px; margin-bottom: 20px; }
      .kpi-grid { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
      .kpi-card { border: 1px solid #cbd5e1; padding: 12px 18px; border-radius: 8px; min-width: 130px; }
      .kpi-label { font-size: 10px; color: #64748b; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 4px; }
      .kpi-value { font-size: 20px; font-weight: 700; color: #0f172a; }
      .section-title, .chart-title { font-size: 13px; font-weight: 700; color: #334155; margin: 20px 0 8px; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px; }
      table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
      th { text-align: left; padding: 6px 8px; background: #f1f5f9; color: #334155; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; }
      td { padding: 5px 8px; border-bottom: 1px solid #e2e8f0; color: #1e293b; }
      tr:nth-child(even) td { background: #f8fafc; }
      .footer { margin-top: 32px; font-size: 10px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 8px; }
      @page { margin: 1.5cm; }
    </style>
  </head><body>
    <h1>📊 ${titulo}</h1>
    <div class="subtitulo">Gerado em ${dataHoje} — Designtex Tecidos / CONEXO</div>
    ${conteudo.innerHTML}
    <div class="footer">Gerado automaticamente pelo CONEXO — Inteligência Comercial</div>
  </body></html>`);
  doc.close();

  iframe.onload = () => {
    iframe.contentWindow.focus();
    iframe.contentWindow.print();
    setTimeout(() => iframe.remove(), 2000);
  };
}

// Wrapper visual com botões de PDF (Relatório Completo e Apenas Gráficos)
function PdfWrapper({ children, title = "Relatório CONEXO" }) {
  const rawId = useId ? useId() : `pdf-${Math.random().toString(36).substring(2, 9)}`;
  const containerId = String(rawId).replace(/:/g, "");

  function baixarGraficosApenas() {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Clona e pega apenas gráficos ou elementos visuais
    const clone = container.cloneNode(true);

    // Remove tabelas se existirem
    const tabelas = clone.querySelectorAll(".pdf-tabela");
    tabelas.forEach(t => t.remove());

    const dataHoje = new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" });
    const anterior = document.getElementById("conexo-print-frame");
    if (anterior) anterior.remove();

    const iframe = document.createElement("iframe");
    iframe.id = "conexo-print-frame";
    iframe.style.cssText = "position:fixed;top:-9999px;left:-9999px;width:900px;height:1px;border:none;visibility:hidden;";
    document.body.appendChild(iframe);

    const doc = iframe.contentDocument || iframe.contentWindow.document;
    doc.open();
    doc.write(`<!DOCTYPE html><html lang="pt-BR"><head>
      <meta charset="UTF-8"/>
      <title>Gráficos — ${title} (${dataHoje})</title>
      <style>
        body { font-family: Arial, sans-serif; color: #1a1a2e; background: white; padding: 24px; font-size: 13px; }
        h1 { font-size: 20px; color: #0f172a; margin-bottom: 4px; }
        .subtitulo { color: #64748b; font-size: 12px; margin-bottom: 20px; }
        .chart-title { font-size: 14px; font-weight: 700; color: #0f172a; margin: 16px 0 8px; border-bottom: 2px solid #38bdf8; padding-bottom: 4px; }
        .chart-wrapper { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
        .kpi-grid { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
        .kpi-card { border: 1px solid #cbd5e1; padding: 12px 18px; border-radius: 8px; min-width: 130px; }
        .kpi-label { font-size: 10px; color: #64748b; text-transform: uppercase; margin-bottom: 4px; }
        .kpi-value { font-size: 20px; font-weight: 700; color: #0f172a; }
        .footer { margin-top: 32px; font-size: 10px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 8px; }
        @page { margin: 1.5cm; }
      </style>
    </head><body>
      <h1>📊 Gráficos executivos — ${title}</h1>
      <div class="subtitulo">Gerado em ${dataHoje} — Designtex Tecidos / CONEXO</div>
      ${clone.innerHTML}
      <div class="footer">Gerado automaticamente pelo CONEXO — Inteligência Comercial</div>
    </body></html>`);
    doc.close();

    iframe.onload = () => {
      iframe.contentWindow.focus();
      iframe.contentWindow.print();
      setTimeout(() => iframe.remove(), 2000);
    };
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 12 }}>
      <div className="no-print" style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button
          onClick={() => baixarPDFUniversal(containerId, title)}
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
          onClick={baixarGraficosApenas}
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
    </div>
  );
}

// ── Roteador principal de dashboards ───────────────────────
export default function Dashboard({ intent, dados }) {
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
      content = <BarrasIntent dados={listaDados} nameKey="vendedor" valKey="faturamento" title="Ranking de Vendedores" />;
      title = "Ranking de Vendedores";
      break;

    case "nexo_top_clientes":
      content = <BarrasIntent dados={listaDados} nameKey="cliente" valKey="faturamento" title="Top Clientes" />;
      title = "Top Clientes";
      break;

    case "nexo_top_produtos":
      content = <BarrasIntent dados={listaDados} nameKey="produto" valKey="faturamento" title="Top Produtos" />;
      title = "Top Produtos";
      break;

    case "nexo_vendas_regiao":
      content = <BarrasIntent dados={listaDados} nameKey="uf" valKey="faturamento" title="Vendas por Estado" />;
      title = "Vendas por Estado";
      break;

    case "nexo_consulta_estoque": {
      if (listaDados.length === 0) return null;
      const sample = listaDados[0] || {};
      const nameKey = sample.cor ? "cor" : sample.descricao ? "descricao" : "cod_produto";
      content = (
        <div>
          <TabelaSimples dados={listaDados} titulo="Disponibilidade de Estoque (Pronto-Entrega)" />
          <BarrasIntent dados={listaDados} nameKey={nameKey} valKey="quantidade_disponivel" title="Metros Disponíveis em Estoque" />
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
          <BarrasIntent dados={listaDados} nameKey={nameKey} valKey="quantidade_solicitada" title="Metragem Programada por Tecido" />
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
      
      const numericCandidates = ["quantidade_disponivel", "quantidade_solicitada", "valor_nf", "valor_total", "faturamento", "valor", "total", "metros", "quantidade", "quantidade_total"];
      let valKey = keys.find(k => numericCandidates.includes(k.toLowerCase()));
      if (!valKey) {
        valKey = keys.find(k => typeof firstRow[k] === "number");
      }
      
      const textCandidates = ["descricao", "nome_tecido", "nome_cor", "cor", "totvs_order_code", "cliente_nome", "cliente", "representante_nome", "vendedor", "nome", "uf", "produto", "artigo"];
      let nameKey = keys.find(k => textCandidates.includes(k.toLowerCase()));
      if (!nameKey) {
        nameKey = keys.find(k => typeof firstRow[k] === "string" && !k.toLowerCase().includes("data") && !k.toLowerCase().includes("created"));
      }
      
      content = (
        <div>
          <TabelaSimples dados={listaDados} titulo="Dados Consultados" />
          {valKey && nameKey && <BarrasIntent dados={listaDados} nameKey={nameKey} valKey={valKey} title="Visualização Gráfica" />}
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

// Tabela simples para exibir lista de linhas no relatório PDF
function TabelaSimples({ dados, titulo }) {
  if (!Array.isArray(dados) || dados.length === 0) return null;
  const colunas = Object.keys(dados[0]);

  // Calcula totais das colunas numéricas
  const totais = {};
  colunas.forEach((col) => {
    const isNum = dados.every((r) => r[col] == null || typeof r[col] === "number" || !isNaN(Number(r[col])));
    if (isNum) {
      const soma = dados.reduce((acc, curr) => acc + (Number(curr[col]) || 0), 0);
      totais[col] = soma;
    }
  });

  const fmt = (v, col) => {
    if (typeof v === "number" || (!isNaN(Number(v)) && typeof v !== "string")) {
      const num = Number(v);
      const isMeter = col && (
        col.toLowerCase().includes("metr") ||
        col.toLowerCase().includes("quantidade") ||
        col.toLowerCase().includes("qtd") ||
        col.toLowerCase().includes("metros")
      );
      return isMeter ? meters(num) : num > 100 ? brl(num) : num.toLocaleString("pt-BR");
    }
    return String(v ?? "—");
  };

  return (
    <div className="pdf-tabela" style={{ marginTop: 8 }}>
      {titulo && <div className="chart-title" style={{ fontSize: 13, fontWeight: 700, color: "#f8fafc", marginBottom: 6 }}>{titulo}</div>}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, color: "#cbd5e1" }}>
        <thead>
          <tr>
            {colunas.map((c) => (
              <th key={c} style={{ textAlign: "left", padding: "6px 8px", borderBottom: "1px solid #334155", color: "#94a3b8", fontWeight: 600, background: "#0f172a" }}>
                {c.replace(/_/g, " ").toUpperCase()}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dados.slice(0, 50).map((row, i) => (
            <tr key={i} style={{ background: i % 2 === 0 ? "transparent" : "#1e293b" }}>
              {colunas.map((c) => (
                <td key={c} style={{ padding: "5px 8px", borderBottom: "1px solid #1e293b" }}>
                  {fmt(row[c], c)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr style={{ background: "#0f172a", borderTop: "2px solid #38bdf8", fontWeight: 700, color: "#f8fafc" }}>
            {colunas.map((c, i) => (
              <td key={c} style={{ padding: "8px", borderBottom: "1px solid #38bdf8" }}>
                {i === 0 ? "TOTAL GERAL" : totais[c] !== undefined ? fmt(totais[c], c) : ""}
              </td>
            ))}
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

