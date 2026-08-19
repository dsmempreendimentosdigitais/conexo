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
          <p>{msg.conteudo}</p>

          {/* Dashboard logo abaixo do texto */}
          {!isUser && msg.intent && msg.dados && (
            <Dashboard intent={msg.intent} dados={msg.dados} />
          )}
        </div>

        {msg.ts && (
          <div className="msg-time">{hora(msg.ts)}</div>
        )}
      </div>
    </div>
  );
}
