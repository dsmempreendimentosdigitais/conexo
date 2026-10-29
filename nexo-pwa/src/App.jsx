import { useState, useEffect } from "react";
import supabase, { login, logout, getSession } from "./auth";
import { cadastrar } from "./api";
import Chat from "./components/Chat";
import AdminPanel from "./components/AdminPanel";

export default function App() {
  const [session,  setSession]  = useState(null);
  const [tab,      setTab]      = useState("login");   // "login" | "cadastro"
  const [loading,  setLoading]  = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [erro,     setErro]     = useState("");
  const [sucesso,  setSucesso]  = useState("");
  const [viewMode, setViewMode] = useState(() => {
    if (typeof window !== "undefined") {
      return window.location.pathname.startsWith("/admin") || window.location.hash.includes("admin")
        ? "admin"
        : "chat";
    }
    return "chat";
  });

  // Listener para sincronização de rota/hash
  useEffect(() => {
    const handleHash = () => {
      if (window.location.hash.includes("admin") || window.location.pathname.startsWith("/admin")) {
        setViewMode("admin");
      } else {
        setViewMode("chat");
      }
    };
    window.addEventListener("hashchange", handleHash);
    return () => window.removeEventListener("hashchange", handleHash);
  }, []);

  // Campos de login
  const [email, setEmail]     = useState("");
  const [senha, setSenha]     = useState("");

  // Campos de cadastro
  const [cnpj,  setCnpj]      = useState("");
  const [setor, setSetor]     = useState("");

  // Recupera sessão existente e ouve mudanças de autenticação (como refresh de token)
  useEffect(() => {
    getSession().then((s) => {
      setSession(s);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  async function handleLogin(e) {
    e.preventDefault();
    setErro(""); setEnviando(true);
    try {
      const s = await login(email, senha);
      setSession(s);
    } catch (err) {
      setErro(err.message);
    } finally {
      setEnviando(false);
    }
  }

  async function handleCadastro(e) {
    e.preventDefault();
    setErro(""); setSucesso(""); setEnviando(true);
    try {
      await cadastrar(cnpj, email, senha, setor);
      setSucesso("Cadastro criado! Confirme seu e-mail e faça login.");
      setTab("login");
    } catch (err) {
      setErro(err.message);
    } finally {
      setEnviando(false);
    }
  }

  async function handleLogout() {
    await logout();
    setSession(null);
  }

  if (loading) {
    return (
      <div style={{ display: "flex", height: "100%", alignItems: "center", justifyContent: "center" }}>
        <div className="typing-indicator">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    );
  }

  if (session) {
    const isMasterAdmin = session.user?.email === "conexo.dev.ai@gmail.com";

    if (viewMode === "admin" && isMasterAdmin) {
      return (
        <AdminPanel
          token={session.access_token}
          onVoltarChat={() => {
            setViewMode("chat");
            window.location.hash = "";
          }}
          onLogout={handleLogout}
        />
      );
    }

    return (
      <Chat
        token={session.access_token}
        email={session.user?.email}
        onLogout={handleLogout}
        onAbrirAdmin={isMasterAdmin ? () => {
          setViewMode("admin");
          window.location.hash = "admin";
        } : null}
      />
    );
  }

  // ── Tela de login / cadastro ──────────────────────────────
  return (
    <div className="login-page">
      <div className="login-card">
        {/* Logo */}
        <div className="login-logo-container">
          <img src="/logo_completo.png" alt="Conexo" className="login-logo-img" />
        </div>

        {/* Abas */}
        <div className="tabs">
          <button className={`tab ${tab === "login" ? "active" : ""}`} onClick={() => { setTab("login"); setErro(""); setSucesso(""); }}>
            Entrar
          </button>
          <button className={`tab ${tab === "cadastro" ? "active" : ""}`} onClick={() => { setTab("cadastro"); setErro(""); setSucesso(""); }}>
            Cadastrar
          </button>
        </div>

        {/* Mensagens */}
        {erro    && <div className="error-msg">⚠️ {erro}</div>}
        {sucesso && <div className="success-msg">✅ {sucesso}</div>}

        {/* Formulário de login */}
        {tab === "login" && (
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label">E-mail</label>
              <input className="form-input" type="email" placeholder="seu@email.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Senha</label>
              <input className="form-input" type="password" placeholder="••••••••" value={senha} onChange={(e) => setSenha(e.target.value)} required />
            </div>
            <button className="btn-primary" type="submit" disabled={enviando}>
              {enviando ? "Entrando…" : "Entrar"}
            </button>
          </form>
        )}

        {/* Formulário de cadastro */}
        {tab === "cadastro" && (
          <form onSubmit={handleCadastro}>
            <div className="form-group">
              <label className="form-label">CNPJ da empresa</label>
              <input className="form-input" type="text" placeholder="00.000.000/0001-00" value={cnpj} onChange={(e) => setCnpj(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Setor</label>
              <input className="form-input" type="text" placeholder="Ex.: Comercial, Diretoria" value={setor} onChange={(e) => setSetor(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">E-mail</label>
              <input className="form-input" type="email" placeholder="seu@email.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Senha (mínimo 6 caracteres)</label>
              <input className="form-input" type="password" placeholder="••••••••" value={senha} onChange={(e) => setSenha(e.target.value)} required minLength={6} />
            </div>
            <button className="btn-primary" type="submit" disabled={enviando}>
              {enviando ? "Criando conta…" : "Criar conta"}
            </button>
            <p style={{ fontSize: 12, color: "var(--text-muted)", textAlign: "center", marginTop: 12 }}>
              O CNPJ precisa ter contrato ativo com o CONEXO.
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
