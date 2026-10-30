import Dashboard from "./Dashboard";
import WhatsAppAudioBubble from "./WhatsAppAudioBubble";

function hora(ts) {
  return new Date(ts).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

export default function Message({ msg, onEnviar, falandoTs, onToggleFala }) {
  const isUser = msg.role === "user";
  const avatarClass = isUser ? "user-av" : "conexo-av";
  const avatarText  = isUser ? "U" : "C";

  // Gera sugestões rápidas de enriquecimento inteligente de dados e gráficos
  const getSugestoes = () => {
    if (isUser || !msg.dados) return [];

    const lista = Array.isArray(msg.dados) ? msg.dados : [msg.dados];
    if (lista.length === 0) return [];

    const first = lista[0] || {};
    const keys = Object.keys(first).map(k => k.toLowerCase());
    const hasCliente = keys.some(k => k.includes("cliente"));
    const hasValor = keys.some(k => k.includes("valor") || k.includes("faturamento") || k.includes("total"));
    const hasOp = keys.some(k => k.includes("op") || k.includes("solicitada") || k.includes("programacao"));
    const hasVendedor = keys.some(k => k.includes("vendedor") || k.includes("representante"));

    const sugestoes = [];

    // Se for lista de clientes sem faturamento ou pergunta sobre clientes
    if (hasCliente && !hasValor) {
      sugestoes.push({
        label: "📊 Ordenar dos maiores compradores para os menores",
        prompt: "Ordene os clientes dos que mais compraram para os que menos compraram com valores faturados e gráfico comparativo"
      });
      sugestoes.push({
        label: "💰 Incluir valores faturados de cada um",
        prompt: "Quais os valores faturados e total de pedidos de cada cliente este ano com gráfico?"
      });
      sugestoes.push({
        label: "⏳ Clientes sem comprar há 60+ dias",
        prompt: "Quais clientes estão sem comprar há mais de 60 dias?"
      });
    } else if (hasCliente && hasValor) {
      sugestoes.push({
        label: "📈 Ver gráfico comparativo em barras",
        prompt: "Mostre o gráfico comparativo em barras do faturamento dos clientes"
      });
      sugestoes.push({
        label: "📦 Produtos mais comprados por esses clientes",
        prompt: "Quais produtos esses clientes mais compraram?"
      });
    } else if (hasOp) {
      sugestoes.push({
        label: "🥧 Gráfico em pizza por artigo (% disponível vs vendido)",
        prompt: "Mostre o gráfico em pizza da produção por artigo e porcentagem disponível vs vendida"
      });
      sugestoes.push({
        label: "📦 Consultar pronta-entrega no estoque",
        prompt: "Tem esses tecidos disponíveis no estoque de pronta-entrega?"
      });
    } else if (hasVendedor) {
      sugestoes.push({
        label: "🎯 Ver atingimento de meta individual",
        prompt: "Qual o percentual de atingimento de meta de cada vendedor?"
      });
      sugestoes.push({
        label: "📉 Vendedores com maior queda vs mês anterior",
        prompt: "Qual vendedor teve a maior queda de vendas comparado com o mês anterior?"
      });
    }

    return sugestoes;
  };

  const sugestoes = getSugestoes();

  return (
    <div className={`message ${msg.role}`}>
      {!isUser && <div className={`msg-avatar ${avatarClass}`}>{avatarText}</div>}

      <div style={{ display: "flex", flexDirection: "column", gap: 4, minWidth: 0 }}>
        <div className="msg-bubble">
          {/* Áudio do Usuário no estilo WhatsApp */}
          {isUser && msg.audioUrl && (
            <WhatsAppAudioBubble
              audioUrl={msg.audioUrl}
              duracaoEstimada={msg.audioDuration}
            />
          )}

          {/* Prioridade #1: Texto da mensagem (com transcrição se veio por voz) */}
          {msg.conteudo && (
            <p
              style={{
                marginTop: isUser && msg.audioUrl ? 8 : 0,
                whiteSpace: "pre-line",
                fontSize: isUser && msg.audioUrl ? 13 : undefined,
                opacity: isUser && msg.audioUrl ? 0.95 : 1,
              }}
            >
              {isUser && msg.audioUrl ? `🗣️ Transcrição: "${msg.conteudo}"` : msg.conteudo}
            </p>
          )}

          {/* Botão de Áudio (Text-to-Speech) */}
          {!isUser && msg.conteudo && (
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
              <button
                onClick={() => onToggleFala && onToggleFala(msg)}
                style={{
                  background: falandoTs === msg.ts ? "rgba(239, 68, 68, 0.25)" : "rgba(255, 255, 255, 0.06)",
                  border: `1px solid ${falandoTs === msg.ts ? "#ef4444" : "rgba(255, 255, 255, 0.15)"}`,
                  color: falandoTs === msg.ts ? "#fca5a5" : "#94a3b8",
                  padding: "4px 10px",
                  borderRadius: 8,
                  fontSize: 11,
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 5,
                  transition: "all 0.2s"
                }}
                title={falandoTs === msg.ts ? "Parar áudio" : "Ouvir esta resposta em voz alta"}
              >
                {falandoTs === msg.ts ? "⏹️ Parar voz" : "🔊 Ouvir resposta"}
              </button>
            </div>
          )}

          {/* Painel de Dados, Gráficos e Exportação PDF (Disponível sob demanda) */}
          {!isUser && msg.dados && (
            <div style={{ marginTop: 10 }}>
              <Dashboard intent={msg.intent || "nexo_consulta_geral"} dados={msg.dados} pergunta={msg.pergunta || ""} />
            </div>
          )}

          {/* Sugestões Rápidas Interativas para Enriquecer a Análise com 1 toque */}
          {!isUser && sugestoes.length > 0 && (
            <div style={{ marginTop: 14, paddingTop: 10, borderTop: "1px solid rgba(255,255,255,0.08)" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "#38bdf8", marginBottom: 8, display: "flex", alignItems: "center", gap: 4 }}>
                💡 Enriquecer esta análise:
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {sugestoes.map((sug, sIdx) => (
                  <button
                    key={sIdx}
                    onClick={() => onEnviar && onEnviar(sug.prompt)}
                    style={{
                      background: "rgba(56, 189, 248, 0.12)",
                      border: "1px solid rgba(56, 189, 248, 0.4)",
                      color: "#38bdf8",
                      padding: "6px 12px",
                      borderRadius: 16,
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: "pointer",
                      textAlign: "left",
                      transition: "all 0.2s",
                      boxShadow: "0 1px 3px rgba(0,0,0,0.2)"
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "#38bdf8";
                      e.currentTarget.style.color = "#0f172a";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "rgba(56, 189, 248, 0.12)";
                      e.currentTarget.style.color = "#38bdf8";
                    }}
                  >
                    {sug.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {msg.ts && (
          <div className="msg-time">{hora(msg.ts)}</div>
        )}
      </div>
    </div>
  );
}
