import { useState, useRef, useEffect, useCallback } from "react";
import { perguntarStream, transcrever, buscarAlertas } from "../api";
import Message from "./Message";
import AlertPanel from "./AlertPanel";

const BOAS_VINDAS = {
  role: "conexo",
  conteudo:
    "Olá! Sou o **CONEXO**, seu analista comercial. Pergunte sobre vendas, " +
    "clientes, produtos, metas ou mercado — por texto ou áudio. 🎙️",
  ts: Date.now(),
};

export default function Chat({ token, email, onLogout }) {
  const [msgs,     setMsgs]     = useState([BOAS_VINDAS]);
  const [input,    setInput]    = useState("");
  const [loading,  setLoading]  = useState(false);
  const [gravando, setGravando] = useState(false);
  const [alertas,  setAlertas]  = useState([]);
  const [showAlerts, setShowAlerts] = useState(false);

  const recRef   = useRef(null);
  const fimRef   = useRef(null);
  const inputRef = useRef(null);

  // Scroll automático ao fim
  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);

  // Busca alertas ao abrir
  useEffect(() => {
    buscarAlertas(token).then(setAlertas);
  }, [token]);

  // Histórico das últimas 6 trocas para contexto do roteador
  const historico = msgs
    .filter((m) => m.role === "user" || m.role === "conexo")
    .slice(-6)
    .map((m) => ({ role: m.role, conteudo: m.conteudo }));

  const enviar = useCallback(
    async (textoPronto) => {
      const texto = (textoPronto ?? input).trim();
      if (!texto || loading) return;
      setInput("");

      const now = Date.now();
      const msgUser = { role: "user", conteudo: texto, ts: now };
      setMsgs((m) => [...m, msgUser]);
      setLoading(true);

      // Cria bolha de streaming vazia para o CONEXO
      const idxConexo = now + 1;
      setMsgs((m) => [
        ...m,
        { role: "conexo", conteudo: "", intent: null, dados: null, ts: idxConexo },
      ]);

      let dadosBuffer = null;
      let intentBuffer = null;

      try {
        await perguntarStream(
          texto,
          historico,
          token,
          // onDados — chega antes do texto
          (intent, dados) => {
            dadosBuffer  = dados;
            intentBuffer = intent;
            setMsgs((m) =>
              m.map((msg) =>
                msg.ts === idxConexo
                  ? { ...msg, intent, dados }
                  : msg
              )
            );
          },
          // onDelta — tokens de texto em tempo real
          (delta) => {
            setMsgs((m) =>
              m.map((msg) =>
                msg.ts === idxConexo
                  ? { ...msg, conteudo: msg.conteudo + delta }
                  : msg
              )
            );
          },
          // onFim
          () => setLoading(false)
        );
      } catch (e) {
        setMsgs((m) =>
          m.map((msg) =>
            msg.ts === idxConexo
              ? { ...msg, conteudo: `⚠️ ${e.message}` }
              : msg
          )
        );
        setLoading(false);
      }
    },
    [input, loading, historico, token]
  );

  // Gravar / parar áudio com compatibilidade mobile universal (iOS / Android)
  async function toggleAudio() {
    if (gravando) {
      recRef.current?.stop();
      setGravando(false);
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Detecta mimeType suportado pelo navegador (Safari iOS vs Chrome Android vs Firefox)
      let options = {};
      const preferredTypes = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
        "audio/aac",
        "audio/ogg",
      ];
      for (const t of preferredTypes) {
        if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(t)) {
          options = { mimeType: t };
          break;
        }
      }

      const rec = new MediaRecorder(stream, options);
      const actualType = rec.mimeType || options.mimeType || "audio/mp4";
      const chunks = [];

      rec.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunks, { type: actualType });
        setLoading(true);
        try {
          const texto = await transcrever(blob, token);
          if (texto && texto.trim()) {
            await enviar(texto);
          } else {
            setLoading(false);
          }
        } catch (e) {
          setMsgs((m) => [
            ...m,
            { role: "conexo", conteudo: `⚠️ ${e.message}`, ts: Date.now() },
          ]);
          setLoading(false);
        }
      };

      recRef.current = rec;
      rec.start();
      setGravando(true);
    } catch (err) {
      alert("Não foi possível acessar o microfone. Verifique as permissões do seu navegador.");
    }
  }

  const initials = email ? email[0].toUpperCase() : "U";

  return (
    <div className="app">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <img src="/logo_icone.png" alt="Conexo" className="logo-icon-img" />
          <span className="logo-text">CONEXO</span>
        </div>

        <button className="sidebar-new-chat" onClick={() => setMsgs([BOAS_VINDAS])}>
          + Nova conversa
        </button>

        <div className="sidebar-section-title">Sugestões</div>
        <div className="chat-history">
          {[
            "Como estão as vendas e metragens este mês?",
            "Quais são os representantes abaixo da meta?",
            "Quais são os produtos mais faturados este ano?",
            "Quais são as cores mais vendidas?",
            "Quais clientes estão inativos há mais de 90 dias?",
          ].map((s) => (
            <div
              key={s}
              className="chat-history-item"
              onClick={() => enviar(s)}
            >
              {s}
            </div>
          ))}
        </div>

        <div className="sidebar-user">
          <div className="user-avatar">{initials}</div>
          <div className="user-info">
            <div className="user-name">{email}</div>
            <div className="user-role">Gestor</div>
          </div>
          <button className="logout-btn" onClick={onLogout} title="Sair">⇠</button>
        </div>
      </aside>

      {/* ── Área principal ── */}
      <div className="main-area">
        {/* Header */}
        <div className="chat-header">
          <div>
            <div className="chat-header-title">CONEXO</div>
            <div className="chat-header-status">
              <span className="status-dot" />
              Online
            </div>
          </div>
          <button
            className="alert-badge"
            onClick={() => setShowAlerts(true)}
            title="Alertas proativos"
          >
            🔔
            {alertas.length > 0 && (
              <span className="alert-count">{alertas.length}</span>
            )}
          </button>
        </div>

        {/* Mensagens */}
        <div className="messages-area">
          {msgs.map((m, i) => (
            <Message key={i} msg={m} />
          ))}

          {loading && msgs[msgs.length - 1]?.conteudo === "" && (
            <div className="message conexo">
              <div className="msg-avatar conexo-av">C</div>
              <div className="typing-indicator">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}
          <div ref={fimRef} />
        </div>

        {/* Input */}
        <div className="input-area">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              className="chat-input"
              rows={1}
              placeholder="Pergunte ao CONEXO… (Enter para enviar)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  enviar();
                }
              }}
            />
            <button
              className={`btn-icon btn-record ${gravando ? "recording" : ""}`}
              onClick={toggleAudio}
              title={gravando ? "Parar gravação" : "Gravar áudio"}
            >
              🎙️
            </button>
            <button
              className="btn-icon btn-send"
              onClick={() => enviar()}
              disabled={loading || !input.trim()}
              title="Enviar"
            >
              ➤
            </button>
          </div>
          <div className="input-hint">
            Shift+Enter para nova linha · 🎙️ para voz · dados sempre do seu banco
          </div>
        </div>
      </div>

      {/* Painel de alertas */}
      {showAlerts && (
        <AlertPanel
          token={token}
          onClose={() => { setShowAlerts(false); buscarAlertas(token).then(setAlertas); }}
        />
      )}
    </div>
  );
}
