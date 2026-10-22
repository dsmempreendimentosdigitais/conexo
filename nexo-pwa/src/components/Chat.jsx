import { useState, useRef, useEffect, useCallback } from "react";
import { perguntarStream, transcrever, buscarAlertas, falar } from "../api";
import Message from "./Message";
import AlertPanel from "./AlertPanel";

const BOAS_VINDAS = {
  role: "conexo",
  conteudo:
    "Olá! Sou o **CONEXO**, seu analista comercial. Pergunte sobre vendas, " +
    "clientes, produtos, metas ou mercado — por texto ou voz.",
  ts: Date.now(),
};

function getStorageKey(email) {
  return `conexo_chats_${email || "guest"}`;
}

const PERGUNTAS_CATEGORIZADAS = [
  {
    categoria: "Desempenho de vendas e Metas",
    icone: "📈",
    perguntas: [
      { label: "Quanto vendemos hoje, esta semana, este mês?", prompt: "Quanto vendemos hoje, esta semana e este mês?" },
      { label: "Como estamos vs mês passado e ano passado?", prompt: "Como estamos vs mês passado e vs mesmo período do ano passado?" },
      { label: "Estamos atingindo a meta de vendas?", prompt: "Estamos atingindo a meta de vendas e qual a projeção para o mês?" },
    ]
  },
  {
    categoria: "Vendedores e Equipe",
    icone: "👥",
    perguntas: [
      { label: "Qual vendedor vendeu mais e qual caiu mais?", prompt: "Qual vendedor vendeu mais e qual teve a maior queda?" },
      { label: "Quais vendedores estão abaixo da meta/histórico?", prompt: "Quais vendedores estão abaixo da meta ou do histórico comercial?" },
    ]
  },
  {
    categoria: "Clientes e Oportunidades",
    icone: "🤝",
    perguntas: [
      { label: "Quais mais compraram este mês?", prompt: "Quais clientes mais compraram este mês?" },
      { label: "Quais pararam de comprar ou tão comprando menos?", prompt: "Quais clientes pararam de comprar ou estão comprando menos?" },
      { label: "Quais estão há mais de 60 dias sem comprar?", prompt: "Quais clientes estão há mais de 60 dias sem comprar?" },
      { label: "Quais clientes priorizar hoje e produtos a oferecer?", prompt: "Quais clientes eu deveria priorizar hoje e quais produtos oferecer para eles?" },
      { label: "Quais oportunidades de vendas o CONEXO enxerga?", prompt: "Quais oportunidades de vendas o CONEXO enxerga que talvez eu não esteja vendo?" },
    ]
  },
  {
    categoria: "Produtos e Estoque",
    icone: "📦",
    perguntas: [
      { label: "Quais vendem mais e quais vendem menos?", prompt: "Quais produtos vendem mais e quais vendem menos?" },
      { label: "Quais estão parados em estoque?", prompt: "Quais produtos estão parados no estoque de pronto-entrega?" },
      { label: "Quais estão perto de acabar em estoque?", prompt: "Quais produtos estão perto de acabar em estoque?" },
      { label: "Quais produtos têm estoque alto e vendas baixas?", prompt: "Quais produtos têm estoque alto e vendas baixas?" },
    ]
  },
  {
    categoria: "Gestão e Regiões",
    icone: "🌐",
    perguntas: [
      { label: "Por que as vendas caíram?", prompt: "Por que as vendas caíram e qual região ou produto mais impactou?" },
      { label: "Qual região tá crescendo mais?", prompt: "Qual região ou estado está crescendo mais este mês?" },
      { label: "Impacto do algodão, frete, dólar e China?", prompt: "Como o preço do algodão, frete, dólar e a China impactam o nosso mercado?" },
    ]
  }
];

const CHIPS_RAPIDOS = [
  { label: "📈 Vendas do Mês", prompt: "Quanto vendemos hoje, esta semana e este mês?" },
  { label: "🎯 Meta Comercial", prompt: "Estamos atingindo a meta de vendas e qual a projeção para o mês?" },
  { label: "👥 Vendedores em Queda", prompt: "Qual vendedor vendeu mais e qual teve a maior queda?" },
  { label: "🤝 Inativos (60+ dias)", prompt: "Quais clientes estão há mais de 60 dias sem comprar?" },
  { label: "📦 Estoque Parado", prompt: "Quais produtos têm estoque alto e vendas baixas?" },
  { label: "🔮 Oportunidades do Dia", prompt: "Quais oportunidades de vendas o CONEXO enxerga que talvez eu não esteja vendo?" },
];

export default function Chat({ token, email, onLogout }) {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [msgs, setMsgs] = useState([BOAS_VINDAS]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [gravando, setGravando] = useState(false);
  const [alertas, setAlertas] = useState([]);
  const [showAlerts, setShowAlerts] = useState(false);
  const [openGroups, setOpenGroups] = useState([0, 1, 2, 3, 4]); // Todas as 5 categorias abertas por padrão

  const toggleGroup = (idx) => {
    setOpenGroups((prev) =>
      prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
    );
  };

  const recRef = useRef(null);
  const fimRef = useRef(null);
  const inputRef = useRef(null);

  // Carrega histórico de chats do localStorage ao iniciar
  useEffect(() => {
    const storageKey = getStorageKey(email);
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setChats(parsed);
          setActiveChatId(parsed[0].id);
          setMsgs(parsed[0].msgs || [BOAS_VINDAS]);
          return;
        }
      }
    } catch (e) {
      console.error("Erro ao carregar chats do localStorage:", e);
    }

    // Se não houver chat salvo, cria o primeiro
    const firstId = `chat_${Date.now()}`;
    const initialChat = {
      id: firstId,
      titulo: "Nova Conversa",
      criadoEm: Date.now(),
      msgs: [BOAS_VINDAS],
    };
    setChats([initialChat]);
    setActiveChatId(firstId);
    setMsgs([BOAS_VINDAS]);
  }, [email]);

  // Salva chats no localStorage sempre que `chats` ou `msgs` mudar
  const salvarChatsNoStorage = useCallback((novosChats) => {
    const storageKey = getStorageKey(email);
    try {
      localStorage.setItem(storageKey, JSON.stringify(novosChats));
    } catch (e) {
      console.error("Erro ao salvar chats:", e);
    }
  }, [email]);

  // Atualiza as mensagens do chat ativo e gera título automático se necessário
  useEffect(() => {
    if (!activeChatId) return;

    setChats((prevChats) => {
      const idx = prevChats.findIndex((c) => c.id === activeChatId);
      if (idx === -1) return prevChats;

      const chatAtual = prevChats[idx];
      let novoTitulo = chatAtual.titulo;

      // Gera título baseado na primeira pergunta do usuário se o título ainda for genérico
      if (novoTitulo === "Nova Conversa" || !novoTitulo) {
        const primeiraPerg = msgs.find((m) => m.role === "user");
        if (primeiraPerg && primeiraPerg.conteudo) {
          novoTitulo = primeiraPerg.conteudo.slice(0, 30) + (primeiraPerg.conteudo.length > 30 ? "..." : "");
        }
      }

      const atualizado = {
        ...chatAtual,
        titulo: novoTitulo,
        msgs: msgs,
        atualizadoEm: Date.now(),
      };

      const novos = [...prevChats];
      novos[idx] = atualizado;
      salvarChatsNoStorage(novos);
      return novos;
    });
  }, [msgs, activeChatId, salvarChatsNoStorage]);

  // Alternar entre conversas salvas no histórico
  const selecionarChat = (chatId) => {
    if (chatId === activeChatId) return;
    const chatEncontrado = chats.find((c) => c.id === chatId);
    if (chatEncontrado) {
      setActiveChatId(chatId);
      setMsgs(chatEncontrado.msgs || [BOAS_VINDAS]);
    }
  };

  // Botão + Nova Conversa
  const novaConversa = () => {
    const novoId = `chat_${Date.now()}`;
    const novoChat = {
      id: novoId,
      titulo: "Nova Conversa",
      criadoEm: Date.now(),
      msgs: [BOAS_VINDAS],
    };

    setChats((prev) => [novoChat, ...prev]);
    setActiveChatId(novoId);
    setMsgs([BOAS_VINDAS]);
  };

  // Apagar uma conversa do histórico
  const apagarChat = (e, chatId) => {
    e.stopPropagation();
    const restantes = chats.filter((c) => c.id !== chatId);
    if (restantes.length === 0) {
      novaConversa();
    } else {
      setChats(restantes);
      salvarChatsNoStorage(restantes);
      if (activeChatId === chatId) {
        setActiveChatId(restantes[0].id);
        setMsgs(restantes[0].msgs || [BOAS_VINDAS]);
      }
    }
  };

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

  const [falandoTs, setFalandoTs] = useState(null);

  const audioRef = useRef(null);

  const pararFala = useCallback(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setFalandoTs(null);
  }, []);

  // Fallback: voz do navegador, priorizando vozes masculinas pt-BR
  const falarNavegador = useCallback((textoLimpo, ts) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      setFalandoTs(null);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(textoLimpo);
    utterance.lang = "pt-BR";
    utterance.rate = 1.0;
    utterance.pitch = 0.85;
    const voices = window.speechSynthesis.getVoices().filter((v) => v.lang?.toLowerCase().startsWith("pt"));
    const masculinas = /(daniel|ricardo|antonio|antônio|felipe|thiago|male|masculin|google português do brasil)/i;
    const voz = voices.find((v) => masculinas.test(v.name)) || voices[0];
    if (voz) utterance.voice = voz;
    utterance.onend = () => setFalandoTs(null);
    utterance.onerror = () => setFalandoTs(null);
    setFalandoTs(ts || true);
    window.speechSynthesis.speak(utterance);
  }, []);

  const falarTexto = useCallback(async (texto, ts) => {
    pararFala();

    // Remove markdown, links, tabelas e sugestões para leitura fluida e natural
    const textoLimpo = (texto || "")
      .replace(/💡\s*\*{0,2}Sugestões.*$/is, "")
      .replace(/\|/g, " ")
      .replace(/[*#_`~>]/g, "")
      .replace(/https?:\/\/\S+/g, "")
      .replace(/[^\w\s\d.,!?;:%$áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ-]/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 4500);

    if (!textoLimpo) return;
    setFalandoTs(ts || true);

    // Cria e "destrava" o elemento de áudio ainda dentro do toque do usuário (exigência do iOS Safari)
    const audio = new Audio();
    audio.src = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA=";
    audio.play().catch(() => {});
    audioRef.current = audio;

    try {
      const blob = await falar(textoLimpo, token);
      if (audioRef.current !== audio) return; // usuário parou/trocou durante o carregamento
      const url = URL.createObjectURL(blob);
      audio.onended = () => {
        URL.revokeObjectURL(url);
        audioRef.current = null;
        setFalandoTs(null);
      };
      audio.onerror = () => {
        URL.revokeObjectURL(url);
        falarNavegador(textoLimpo, ts);
      };
      audio.src = url;
      await audio.play();
    } catch (e) {
      if (audioRef.current !== audio) return;
      console.warn("TTS servidor indisponível, usando voz do navegador:", e);
      falarNavegador(textoLimpo, ts);
    }
  }, [token, pararFala, falarNavegador]);

  const toggleFalaMsg = useCallback((m) => {
    if (falandoTs === m.ts) {
      pararFala();
    } else {
      falarTexto(m.conteudo, m.ts);
    }
  }, [falandoTs, pararFala, falarTexto]);

  const enviar = useCallback(
    async (textoPronto, opcoes = {}) => {
      const texto = (textoPronto ?? input).trim();
      const veioPorAudio = opcoes?.veioPorAudio || false;
      if (!texto || loading) return;
      setInput("");
      if (inputRef.current) {
        inputRef.current.style.height = "auto";
      }

      // Se CONEXO estava falando, para a fala ao enviar nova pergunta
      pararFala();

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

      let conteudoAcumulado = "";

      try {
        await perguntarStream(
          texto,
          historico,
          token,
          // onDados — chega antes do texto
          (intent, dados) => {
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
            conteudoAcumulado += delta;
            setMsgs((m) =>
              m.map((msg) =>
                msg.ts === idxConexo
                  ? { ...msg, conteudo: msg.conteudo + delta }
                  : msg
              )
            );
          },
          // onFim
          () => {
            setLoading(false);
            if (veioPorAudio && conteudoAcumulado) {
              falarTexto(conteudoAcumulado, idxConexo);
            }
          }
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
    [input, loading, historico, token, pararFala, falarTexto]
  );

  // Gravar / parar áudio com compatibilidade mobile universal (iOS Safari / Android Chrome / Desktop)
  async function toggleAudio() {
    if (gravando && recRef.current) {
      try {
        if (recRef.current.state !== "inactive") {
          recRef.current.stop();
        }
      } catch (e) {
        console.warn("stop error:", e);
      }
      setGravando(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      const isIOS =
        typeof navigator !== "undefined" &&
        (/iPad|iPhone|iPod/.test(navigator.userAgent) ||
          (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1));

      let options = {};
      const preferredTypes = isIOS
        ? ["audio/mp4", "audio/aac"]
        : [
            "audio/webm;codecs=opus",
            "audio/webm",
            "audio/ogg",
            "audio/mp4",
          ];

      for (const t of preferredTypes) {
        if (
          typeof MediaRecorder !== "undefined" &&
          MediaRecorder.isTypeSupported(t)
        ) {
          options = { mimeType: t };
          break;
        }
      }

      const rec = new MediaRecorder(stream, options);
      const actualType = rec.mimeType || options.mimeType || (isIOS ? "audio/mp4" : "audio/webm");
      const chunks = [];

      rec.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunks, { type: actualType });

        if (!blob || blob.size < 200) {
          setMsgs((m) => [
            ...m,
            {
              role: "conexo",
              conteudo:
                "⚠️ Áudio muito curto ou microfone sem sinal. Por favor, toque no botão de voz e fale sua pergunta com clareza.",
              ts: Date.now(),
            },
          ]);
          return;
        }

        setLoading(true);
        try {
          const texto = await transcrever(blob, token);
          if (texto && texto.trim()) {
            await enviar(texto, { veioPorAudio: true });
          } else {
            setMsgs((m) => [
              ...m,
              {
                role: "conexo",
                conteudo:
                  "⚠️ Não identifiquei fala audível no áudio. Fale mais próximo ao microfone do celular e tente novamente.",
                ts: Date.now(),
              },
            ]);
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
      // Inicia captura contínua com chunks de 250ms
      rec.start(250);
      setGravando(true);
    } catch (err) {
      alert(
        "Não foi possível acessar o microfone. Verifique se a permissão de áudio está liberada no seu navegador (ícone de cadeado na barra de endereços)."
      );
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

        <button className="sidebar-new-chat" onClick={novaConversa}>
          + Nova conversa
        </button>

        {/* ── Seção de Histórico de Conversas ── */}
        <div className="sidebar-section-title">Histórico de Conversas</div>
        <div className="chat-history">
          {chats.map((c) => (
            <div
              key={c.id}
              className={`chat-history-item ${c.id === activeChatId ? "active" : ""}`}
              onClick={() => selecionarChat(c.id)}
              style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
            >
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>
                💬 {c.titulo}
              </span>
              {chats.length > 1 && (
                <button
                  onClick={(e) => apagarChat(e, c.id)}
                  title="Apagar conversa"
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    fontSize: 12,
                    padding: "2px 4px",
                    marginLeft: 4,
                  }}
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>

        {/* ── Seção de Perguntas Padrão (Categorias Estratégicas de Gestão) ── */}
        <div className="sidebar-section-title" style={{ marginTop: 12 }}>Atalhos de Gestão</div>
        <div className="sidebar-prompts-container">
          {PERGUNTAS_CATEGORIZADAS.map((grp, gIdx) => {
            const isOpen = openGroups.includes(gIdx);
            return (
              <div key={grp.categoria} className="prompt-group">
                <div
                  className="prompt-group-header"
                  onClick={() => toggleGroup(gIdx)}
                >
                  <span>{grp.icone} {grp.categoria}</span>
                  <span style={{ fontSize: 10, opacity: 0.7 }}>{isOpen ? "▲" : "▼"}</span>
                </div>
                {isOpen && (
                  <div style={{ marginTop: 2 }}>
                    {grp.perguntas.map((p, pIdx) => (
                      <div
                        key={pIdx}
                        className="prompt-item"
                        onClick={() => enviar(p.prompt)}
                        title={p.prompt}
                      >
                        • {p.label}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
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
            <Message
              key={i}
              msg={m}
              onEnviar={enviar}
              falandoTs={falandoTs}
              onToggleFala={toggleFalaMsg}
            />
          ))}

          {/* Banner de Fala Ativa (se o CONEXO estiver respondendo em áudio) */}
          {falandoTs && (
            <div
              style={{
                position: "sticky",
                bottom: 8,
                alignSelf: "center",
                background: "#0f172a",
                border: "1px solid #38bdf8",
                color: "#38bdf8",
                padding: "8px 16px",
                borderRadius: 20,
                fontSize: 12,
                fontWeight: 700,
                display: "flex",
                alignItems: "center",
                gap: 10,
                boxShadow: "0 4px 14px rgba(0,0,0,0.4)",
                zIndex: 20,
              }}
            >
              <span className="pulse-dot">🔊</span>
              <span>CONEXO falando em áudio...</span>
              <button
                onClick={pararFala}
                style={{
                  background: "#ef4444",
                  color: "#ffffff",
                  border: "none",
                  padding: "4px 10px",
                  borderRadius: 12,
                  fontSize: 11,
                  fontWeight: 800,
                  cursor: "pointer",
                }}
              >
                ⏹️ Parar voz
              </button>
            </div>
          )}

          {/* Empty State / Cards Interativos de Perguntas Estratégicas quando só há boas-vindas */}
          {msgs.length === 1 && (
            <div className="empty-state-container">
              <div className="empty-title">🎯 Central de Tomada de Decisão</div>
              <div className="empty-subtitle">
                Selecione uma análise estratégica rápida ou pergunte qualquer informação comercial por texto ou voz.
              </div>

              <div className="prompt-cards-grid">
                {[
                  {
                    cat: "📈 Vendas & Desempenho",
                    icon: "📈",
                    prompt: "Quanto vendemos hoje, esta semana e este mês? Como estamos vs mês passado e ano passado?",
                  },
                  {
                    cat: "👥 Equipe Comercial",
                    icon: "👥",
                    prompt: "Qual vendedor vendeu mais e qual teve a maior queda? Quais estão abaixo da meta?",
                  },
                  {
                    cat: "🤝 Clientes & Oportunidades",
                    icon: "🤝",
                    prompt: "Quais clientes estão há mais de 60 dias sem comprar e quais oportunidades eu deveria priorizar hoje?",
                  },
                  {
                    cat: "📦 Produtos & Estoque",
                    icon: "📦",
                    prompt: "Quais produtos vendem mais e quais estão com estoque alto e vendas baixas?",
                  },
                  {
                    cat: "🌐 Regiões & Tendências",
                    icon: "🌐",
                    prompt: "Qual região ou estado está crescendo mais este mês e por que as vendas subiram ou caíram?",
                  },
                  {
                    cat: "🔮 Oportunidades Ocultas",
                    icon: "🔮",
                    prompt: "Quais oportunidades de vendas o CONEXO enxerga que talvez eu não esteja vendo?",
                  },
                ].map((card, cIdx) => (
                  <div
                    key={cIdx}
                    className="prompt-card"
                    onClick={() => enviar(card.prompt)}
                  >
                    <div className="prompt-card-header">
                      <span>{card.icon}</span>
                      <span>{card.cat}</span>
                    </div>
                    <div className="prompt-card-text">{card.prompt}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

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

        {/* Barra de Chips Rápidos Deslizantes */}
        <div className="prompt-chips-bar">
          {CHIPS_RAPIDOS.map((chip, chIdx) => (
            <div
              key={chIdx}
              className="prompt-chip"
              onClick={() => enviar(chip.prompt)}
            >
              {chip.label}
            </div>
          ))}
        </div>

        {/* Indicador de gravação de áudio */}
        {gravando && (
          <div
            style={{
              padding: "8px 16px",
              background: "linear-gradient(135deg, #10a37f, #0d8a6a)",
              color: "#ffffff",
              fontSize: 12,
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              borderRadius: "8px 8px 0 0",
              margin: "0 16px -8px 16px",
              boxShadow: "0 4px 12px rgba(16, 163, 127, 0.25)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span className="chatgpt-voice-icon" style={{ color: "#fff" }}>
                <span className="wave-bar bar-1" />
                <span className="wave-bar bar-2" />
                <span className="wave-bar bar-3" />
                <span className="wave-bar bar-4" />
              </span>
              <span>Ouvindo... Fale sua pergunta e toque no botão para enviar</span>
            </div>
            <button
              type="button"
              onClick={toggleAudio}
              style={{
                background: "#ffffff",
                color: "#0d8a6a",
                border: "none",
                borderRadius: 4,
                padding: "3px 10px",
                fontWeight: 700,
                cursor: "pointer",
                fontSize: 11,
              }}
            >
              Concluir e Enviar
            </button>
          </div>
        )}

        {/* Input */}
        <div className="input-area">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              className="chat-input"
              rows={2}
              placeholder="Pergunte ao CONEXO… (Enter para enviar)"
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  enviar();
                }
              }}
            />
            <button
              type="button"
              className={`btn-icon btn-record ${gravando ? "recording" : ""}`}
              onClick={toggleAudio}
              title={gravando ? "Parar gravação e enviar" : "Gravar áudio (Voz estilo ChatGPT)"}
              aria-label="Gravar áudio"
            >
              <span className="chatgpt-voice-icon" aria-hidden="true">
                <span className="wave-bar bar-1" />
                <span className="wave-bar bar-2" />
                <span className="wave-bar bar-3" />
                <span className="wave-bar bar-4" />
              </span>
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
            Shift+Enter para nova linha · Toque no ícone de voz para falar · Dados sempre do seu banco
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
