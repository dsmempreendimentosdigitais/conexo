import Dashboard from "./Dashboard";

function hora(ts) {
  return new Date(ts).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

export default function Message({ msg }) {
  const isUser = msg.role === "user";
  const avatarClass = isUser ? "user-av" : "conexo-av";
  const avatarText  = isUser ? "U" : "C";

  return (
    <div className={`message ${msg.role}`}>
      {!isUser && <div className={`msg-avatar ${avatarClass}`}>{avatarText}</div>}

      <div style={{ display: "flex", flexDirection: "column", gap: 4, minWidth: 0 }}>
        <div className="msg-bubble">
          {/* Prioridade #1: Gráfico e Tabela de dados no topo da resposta */}
          {!isUser && msg.dados && (
            <Dashboard intent={msg.intent || "nexo_consulta_geral"} dados={msg.dados} pergunta={msg.pergunta || ""} />
          )}

          {/* Prioridade #2: Texto síntese ultra-resumido em poucas palavras */}
          {msg.conteudo && <p style={{ marginTop: !isUser && msg.dados ? 12 : 0 }}>{msg.conteudo}</p>}
        </div>

        {msg.ts && (
          <div className="msg-time">{hora(msg.ts)}</div>
        )}
      </div>
    </div>
  );
}
