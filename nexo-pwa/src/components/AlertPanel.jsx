import { useState, useEffect } from "react";
import { buscarAlertas, marcarAlertaLido } from "../api";

function tempo(ts) {
  const d = new Date(ts);
  return d.toLocaleString("pt-BR", {
    day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
  });
}

export default function AlertPanel({ token, onClose }) {
  const [alertas, setAlertas] = useState([]);

  useEffect(() => {
    buscarAlertas(token).then(setAlertas);
  }, [token]);

  async function marcar(id) {
    await marcarAlertaLido(id, token);
    setAlertas((a) => a.filter((x) => x.id !== id));
  }

  return (
    <div className="alert-panel-overlay" onClick={onClose}>
      <div className="alert-panel" onClick={(e) => e.stopPropagation()}>
        <div className="alert-panel-header">
          <span className="alert-panel-title">🔔 Alertas proativos</span>
          <button className="alert-panel-close" onClick={onClose}>✕</button>
        </div>

        <div className="alert-list">
          {alertas.length === 0 && (
            <div style={{ textAlign: "center", color: "var(--text-muted)", marginTop: 40, fontSize: 14 }}>
              ✅ Nenhum alerta no momento
            </div>
          )}
          {alertas.map((a) => (
            <div key={a.id} className={`alert-item ${a.severidade}`}>
              <div className="alert-item-type">
                {a.tipo === "mercado" ? "🌐 Mercado" : "📊 Interno"} · {a.severidade.toUpperCase()}
              </div>
              <div className="alert-item-msg">{a.mensagem}</div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 6 }}>
                <span className="alert-item-time">{tempo(a.created_at)}</span>
                <button
                  onClick={() => marcar(a.id)}
                  style={{
                    background: "none", border: "none", color: "var(--text-muted)",
                    fontSize: 12, cursor: "pointer",
                  }}
                >
                  Marcar como lido ✓
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
