import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const brl = (v) =>
  Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const COLORS = ["#38bdf8", "#818cf8", "#34d399", "#fb923c", "#f472b6"];

// ── KPI simples para nexo_vendas_periodo ────────────────────
function KpiCards({ dados }) {
  const d = Array.isArray(dados) ? dados[0] : dados;
  if (!d) return null;

  const items = [
    { label: "Faturamento", value: brl(d.faturamento ?? d.total ?? 0) },
    { label: "Pedidos",     value: Number(d.total_pedidos ?? d.pedidos ?? 0).toLocaleString("pt-BR") },
    { label: "Ticket médio",value: brl(d.ticket_medio ?? d.ticket ?? 0) },
  ];

  return (
    <div className="kpi-grid">
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

  const data = dados.map((r, i) => ({
    nome:  String(r[nameKey] ?? r.nome ?? "—").slice(0, 22),
    valor: Number(r[valKey]  ?? r.faturamento ?? 0),
    fill:  COLORS[i % COLORS.length],
  }));

  return (
    <div className="chart-wrapper">
      {title && <div className="chart-title">{title}</div>}
      <ResponsiveContainer width="100%" height={Math.max(180, data.length * 38)}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="nome"
            width={150}
            tick={{ fill: "#94a3b8", fontSize: 12 }}
          />
          <Tooltip
            formatter={(v) => brl(v)}
            contentStyle={{
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 8,
              fontSize: 13,
            }}
          />
          <Bar dataKey="valor" radius={[0, 6, 6, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
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

// ── Roteador principal de dashboards ───────────────────────
export default function Dashboard({ intent, dados }) {
  if (!dados) return null;

  const cleanIntent = intent ? String(intent).replace("conexo_", "nexo_") : "";

  switch (cleanIntent) {
    case "nexo_vendas_periodo":
      return <KpiCards dados={dados} />;

    case "nexo_comparativo_mes":
    case "nexo_comparativo_ano":
      return <Comparativo dados={dados} />;

    case "nexo_ranking_vendedores":
      return <BarrasIntent dados={dados} nameKey="vendedor" valKey="faturamento" title="Ranking de vendedores" />;

    case "nexo_top_clientes":
      return <BarrasIntent dados={dados} nameKey="cliente" valKey="faturamento" title="Top clientes" />;

    case "nexo_top_produtos":
      return <BarrasIntent dados={dados} nameKey="produto" valKey="faturamento" title="Top produtos" />;

    case "nexo_vendas_regiao":
      return <BarrasIntent dados={dados} nameKey="uf" valKey="faturamento" title="Vendas por estado" />;

    case "nexo_relatorio_periodo":
      return <RelatorioCompleto dados={dados} />;

    case "nexo_consulta_geral": {
      if (!Array.isArray(dados) || dados.length === 0) return null;
      const firstRow = dados[0];
      const keys = Object.keys(firstRow);
      
      const numericCandidates = ["valor_nf", "valor_total", "faturamento", "valor", "total", "metros", "quantidade", "quantidade_total"];
      let valKey = keys.find(k => numericCandidates.includes(k.toLowerCase()));
      if (!valKey) {
        valKey = keys.find(k => typeof firstRow[k] === "number");
      }
      
      const textCandidates = ["totvs_order_code", "cliente_nome", "cliente", "representante_nome", "vendedor", "nome", "uf", "produto", "artigo", "cor"];
      let nameKey = keys.find(k => textCandidates.includes(k.toLowerCase()));
      if (!nameKey) {
        nameKey = keys.find(k => typeof firstRow[k] === "string" && !k.toLowerCase().includes("data") && !k.toLowerCase().includes("created"));
      }
      
      if (valKey && nameKey) {
        return <BarrasIntent dados={dados} nameKey={nameKey} valKey={valKey} title="Visualização dos dados" />;
      }
      return null;
    }

    case "nexo_inteligencia_mercado":
      return typeof dados === "object" && dados.fontes
        ? <Fontes fontes={dados.fontes} />
        : null;

    default:
      return null;
  }
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
  const fmt = (v) => {
    if (typeof v === "number") return Number(v) > 100 ? brl(v) : v.toLocaleString("pt-BR");
    return String(v ?? "—");
  };
  return (
    <div className="pdf-tabela" style={{ marginTop: 8 }}>
      {titulo && <div className="chart-title">{titulo}</div>}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, color: "#cbd5e1" }}>
        <thead>
          <tr>
            {colunas.map((c) => (
              <th key={c} style={{ textAlign: "left", padding: "4px 8px", borderBottom: "1px solid #334155", color: "#94a3b8", fontWeight: 600 }}>
                {c.replace(/_/g, " ").toUpperCase()}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dados.slice(0, 20).map((row, i) => (
            <tr key={i} style={{ background: i % 2 === 0 ? "transparent" : "#1e293b" }}>
              {colunas.map((c) => (
                <td key={c} style={{ padding: "4px 8px", borderBottom: "1px solid #1e293b" }}>
                  {fmt(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Relatório consolidado — múltiplos blocos com botão de PDF
function RelatorioCompleto({ dados }) {
  if (!dados || typeof dados !== "object") return null;

  function baixarPDF() {
    const printCSS = `
      <style>
        @media print {
          body { background: white !important; color: black !important; font-family: Arial, sans-serif; }
          .no-print { display: none !important; }
          .kpi-grid { display: flex; gap: 16px; flex-wrap: wrap; }
          .kpi-card { border: 1px solid #ccc; padding: 12px 20px; border-radius: 8px; min-width: 120px; }
          .kpi-label { font-size: 11px; color: #555; }
          .kpi-value { font-size: 18px; font-weight: bold; color: #111; }
          .chart-title { font-size: 14px; font-weight: bold; margin: 16px 0 8px; color: #333; }
          table { width: 100%; border-collapse: collapse; font-size: 12px; }
          th { text-align: left; padding: 4px 8px; border-bottom: 2px solid #333; color: #333; }
          td { padding: 4px 8px; border-bottom: 1px solid #ccc; }
          h1 { font-size: 20px; margin-bottom: 4px; }
          p { color: #555; font-size: 12px; margin-bottom: 16px; }
        }
      </style>
    `;
    const conteudo = document.getElementById("relatorio-pdf-content");
    const janela = window.open("", "_blank", "width=900,height=700");
    janela.document.write(`
      <html><head><title>Relatório CONEXO</title>${printCSS}</head>
      <body>
        <h1>Relatório CONEXO</h1>
        <p>Gerado em ${new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })}</p>
        ${conteudo ? conteudo.innerHTML : ""}
      </body></html>
    `);
    janela.document.close();
    janela.focus();
    setTimeout(() => { janela.print(); janela.close(); }, 500);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 12 }}>
      <button
        onClick={baixarPDF}
        className="no-print"
        style={{
          alignSelf: "flex-start",
          background: "#38bdf8",
          color: "#0f172a",
          border: "none",
          borderRadius: 8,
          padding: "8px 18px",
          fontWeight: 700,
          fontSize: 14,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: 6,
        }}
      >
        📄 Baixar PDF
      </button>
      <div id="relatorio-pdf-content">
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
      </div>
    </div>
  );
}
