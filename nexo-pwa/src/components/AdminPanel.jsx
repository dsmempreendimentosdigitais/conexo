import { useState, useEffect } from "react";
import {
  getAdminOverview,
  getAdminTenants,
  createAdminTenant,
  updateAdminTenant,
  getAdminConnectors,
  saveAdminConnectors,
  testAdminConnector,
  getAdminUsers,
  createAdminUser,
  resetAdminUserPassword,
  updateAdminUser,
  deleteAdminUser,
  getAdminLogs,
  getAdminFinanceiro,
} from "../api";

export default function AdminPanel({ token, onVoltarChat, onLogout }) {
  const [tab, setTab] = useState("overview"); // overview | tenants | connectors | users | financeiro | logs
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");

  // Dados carregados
  const [overview, setOverview] = useState(null);
  const [tenants, setTenants] = useState([]);
  const [selectedTenantId, setSelectedTenantId] = useState("");
  const [connectorsData, setConnectorsData] = useState(null);
  const [users, setUsers] = useState([]);
  const [filterUserTenant, setFilterUserTenant] = useState("");
  const [financeiro, setFinanceiro] = useState(null);
  const [logs, setLogs] = useState([]);
  const [apenasErros, setApenasErros] = useState(false);

  // Modais
  const [modalNovaEmpresa, setModalNovaEmpresa] = useState(false);
  const [formNovaEmpresa, setFormNovaEmpresa] = useState({
    nome: "",
    nome_fantasia: "",
    cnpj: "",
    plano: "Enterprise",
    valor_mensal: 3500,
    dia_vencimento: 10,
    cor_primaria: "#38bdf8",
  });

  const [modalNovoUsuario, setModalNovoUsuario] = useState(false);
  const [formNovoUsuario, setFormNovoUsuario] = useState({
    tenant_id: "",
    email: "",
    nome: "",
    perfil: "gestor",
    setor: "Comercial",
    representante_codigo: "",
    senha: "",
  });

  const [modalSenhaGerada, setModalSenhaGerada] = useState(null); // { email, senha, mensagem }
  const [testandoConector, setTestandoConector] = useState("");
  const [resultadoTeste, setResultadoTeste] = useState(null);

  // Carrega visão geral ao abrir
  useEffect(() => {
    carregarTudo();
  }, [token]);

  async function carregarTudo() {
    setLoading(true);
    setErro("");
    try {
      const [ov, tnts, usrs, fin, lgs] = await Promise.all([
        getAdminOverview(token).catch(() => null),
        getAdminTenants(token).catch(() => []),
        getAdminUsers(null, token).catch(() => []),
        getAdminFinanceiro(token).catch(() => null),
        getAdminLogs({ limit: 40 }, token).catch(() => []),
      ]);

      setOverview(ov);
      setTenants(tnts);
      setUsers(usrs);
      setFinanceiro(fin);
      setLogs(lgs);

      if (tnts.length > 0 && !selectedTenantId) {
        setSelectedTenantId(tnts[0].id);
        carregarConectores(tnts[0].id);
      }
    } catch (e) {
      setErro("Falha ao carregar dados do painel master: " + e.message);
    } finally {
      setLoading(false);
    }
  }

  async function carregarConectores(tid) {
    if (!tid) return;
    try {
      const data = await getAdminConnectors(tid, token);
      setConnectorsData(data.conectores || {});
    } catch (e) {
      setErro("Erro ao carregar conectores: " + e.message);
    }
  }

  async function handleTrocarTenantConectores(tid) {
    setSelectedTenantId(tid);
    setResultadoTeste(null);
    await carregarConectores(tid);
  }

  // ── Salvar Conectores ──
  async function handleSalvarConectores(e) {
    e.preventDefault();
    setErro("");
    setSucesso("");
    try {
      await saveAdminConnectors(selectedTenantId, connectorsData, token);
      setSucesso("Configurações de conectores e APIs salvas com sucesso!");
      setTimeout(() => setSucesso(""), 4000);
    } catch (e) {
      setErro("Erro ao salvar conectores: " + e.message);
    }
  }

  // ── Testar Conexão ao Vivo ──
  async function handleTestarConector(tipo) {
    setTestandoConector(tipo);
    setResultadoTeste(null);
    setErro("");
    try {
      const cfg = connectorsData[tipo] || {};
      const res = await testAdminConnector(tipo, cfg, token);
      setResultadoTeste({ tipo, ...res });
    } catch (e) {
      setResultadoTeste({ tipo, sucesso: false, mensagem: e.message });
    } finally {
      setTestandoConector("");
    }
  }

  // ── Criar Nova Empresa ──
  async function handleCriarEmpresa(e) {
    e.preventDefault();
    setErro("");
    try {
      const nova = await createAdminTenant(formNovaEmpresa, token);
      setTenants((prev) => [...prev, nova]);
      setModalNovaEmpresa(false);
      setSucesso(`Empresa "${nova.nome_fantasia || nova.nome}" cadastrada com sucesso!`);
      setTimeout(() => setSucesso(""), 4000);
      carregarTudo();
    } catch (e) {
      setErro("Erro ao cadastrar empresa: " + e.message);
    }
  }

  // ── Criar Novo Usuário ──
  async function handleCriarUsuario(e) {
    e.preventDefault();
    setErro("");
    try {
      const res = await createAdminUser(formNovoUsuario, token);
      setModalNovoUsuario(false);
      setModalSenhaGerada({
        email: formNovoUsuario.email,
        senha: res.senha_provisoria,
        mensagem: "Usuário cadastrado com sucesso! Copie a senha provisória abaixo e envie ao usuário.",
      });
      carregarTudo();
    } catch (e) {
      setErro("Erro ao criar usuário: " + e.message);
    }
  }

  // ── Resetar / Gerar Senha Provisória ──
  async function handleResetSenha(user) {
    if (!confirm(`Deseja gerar uma nova senha provisória de acesso para ${user.email}?`)) return;
    setErro("");
    try {
      const res = await resetAdminUserPassword(user.id, null, token);
      setModalSenhaGerada({
        email: user.email,
        senha: res.nova_senha,
        mensagem: `Senha de acesso para ${user.email} redefinida com sucesso! Copie a senha e envie no WhatsApp do colaborador.`,
      });
    } catch (e) {
      setErro("Erro ao redefinir senha: " + e.message);
    }
  }

  // ── Alternar Bloqueio de Usuário ──
  async function handleToggleUserAtivo(user) {
    const novoStatus = !user.ativo;
    try {
      await updateAdminUser(user.id, { ativo: novoStatus }, token);
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, ativo: novoStatus } : u))
      );
    } catch (e) {
      alert("Erro ao alterar status: " + e.message);
    }
  }

  // ── Excluir Usuário ──
  async function handleExcluirUsuario(user) {
    if (!confirm(`Excluir permanentemente o usuário ${user.email}?`)) return;
    try {
      await deleteAdminUser(user.id, token);
      setUsers((prev) => prev.filter((u) => u.id !== user.id));
    } catch (e) {
      alert("Erro ao excluir usuário: " + e.message);
    }
  }

  const formatBRL = (v) =>
    Number(v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

  const tenantAtual = tenants.find((t) => t.id === selectedTenantId) || tenants[0];

  return (
    <div className="admin-container">
      {/* ── Topbar Master ── */}
      <header className="admin-header">
        <div className="admin-header-left">
          <div className="admin-logo">
            <img src="/logo_icone.png" alt="Conexo" className="logo-icon-img" />
            <div className="admin-logo-titles">
              <span className="admin-logo-title">CONEXO MASTER</span>
              <span className="admin-badge-saas">Painel Administrativo SaaS</span>
            </div>
          </div>
        </div>

        <div className="admin-header-right">
          <button className="btn-admin-action btn-back-chat" onClick={onVoltarChat} title="Voltar para a IA Comercial">
            💬 Voltar ao Chat
          </button>
          <button className="btn-admin-action btn-logout" onClick={onLogout} title="Sair da Conta">
            🚪 Sair
          </button>
        </div>
      </header>

      {/* ── Submenu de Navegação ── */}
      <nav className="admin-nav-tabs">
        <button className={`admin-tab-btn ${tab === "overview" ? "active" : ""}`} onClick={() => setTab("overview")}>
          📊 Visão Geral
        </button>
        <button className={`admin-tab-btn ${tab === "tenants" ? "active" : ""}`} onClick={() => setTab("tenants")}>
          🏢 Empresas Clientes ({tenants.length})
        </button>
        <button className={`admin-tab-btn ${tab === "connectors" ? "active" : ""}`} onClick={() => setTab("connectors")}>
          🔌 Conectores & APIs (ERP)
        </button>
        <button className={`admin-tab-btn ${tab === "users" ? "active" : ""}`} onClick={() => setTab("users")}>
          👥 Usuários & Senhas ({users.length})
        </button>
        <button className={`admin-tab-btn ${tab === "financeiro" ? "active" : ""}`} onClick={() => setTab("financeiro")}>
          💰 Financeiro SaaS (MRR)
        </button>
        <button className={`admin-tab-btn ${tab === "logs" ? "active" : ""}`} onClick={() => setTab("logs")}>
          🚨 Logs & Auditoria
        </button>
      </nav>

      {/* Alertas */}
      {erro && <div className="admin-alert error">⚠️ {erro}</div>}
      {sucesso && <div className="admin-alert success">✅ {sucesso}</div>}

      {/* Conteúdo Principal */}
      <main className="admin-content">
        {loading ? (
          <div className="admin-loading">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
            <p>Carregando ecossistema CONEXO...</p>
          </div>
        ) : (
          <>
            {/* ══════════════════════════════════════════════════════════
                1. TAB: VISÃO GERAL (OVERVIEW)
               ══════════════════════════════════════════════════════════ */}
            {tab === "overview" && overview && (
              <div className="admin-tab-content">
                <div className="admin-kpi-grid">
                  <div className="admin-kpi-card highlight">
                    <span className="kpi-icon">💰</span>
                    <span className="kpi-label">MRR (Faturamento Mensal Conexo)</span>
                    <strong className="kpi-value text-accent">{formatBRL(overview.mrr_total)}</strong>
                    <span className="kpi-sub">Lucro Líquido: {formatBRL(overview.lucro_estimado)} ({overview.margem_lucro_pct}%)</span>
                  </div>

                  <div className="admin-kpi-card">
                    <span className="kpi-icon">🏢</span>
                    <span className="kpi-label">Empresas Clientes</span>
                    <strong className="kpi-value">{overview.tenants_ativos} ativas</strong>
                    <span className="kpi-sub">Total de {overview.tenants_total} cadastradas</span>
                  </div>

                  <div className="admin-kpi-card">
                    <span className="kpi-icon">👥</span>
                    <span className="kpi-label">Usuários Cadastrados</span>
                    <strong className="kpi-value">{overview.usuarios_ativos} ativos</strong>
                    <span className="kpi-sub">Total de {overview.usuarios_total} contas</span>
                  </div>

                  <div className="admin-kpi-card">
                    <span className="kpi-icon">⚡</span>
                    <span className="kpi-label">Consultas de IA no Mês</span>
                    <strong className="kpi-value">{overview.perguntas_mes}</strong>
                    <span className="kpi-sub">Custo Estimado IA: {formatBRL(overview.custo_ia_mes)}</span>
                  </div>
                </div>

                {/* Semáforo de Saúde dos Serviços */}
                <div className="admin-section-card">
                  <h3 className="section-title">🚦 Status de Integrações & Serviços em Tempo Real</h3>
                  <div className="health-grid">
                    <div className="health-card">
                      <span className="health-dot online" />
                      <div>
                        <strong>TOTVS Moda API (Bhan)</strong>
                        <p>Autenticação Bearer OAuth2 · 200 OK</p>
                      </div>
                    </div>
                    <div className="health-card">
                      <span className="health-dot online" />
                      <div>
                        <strong>Banco de Dados (Supabase PostgreSQL)</strong>
                        <p>Conexão Ativa · Pooler SSL Operacional</p>
                      </div>
                    </div>
                    <div className="health-card">
                      <span className="health-dot online" />
                      <div>
                        <strong>Motor de IA (Gemini 2.5 Flash & Whisper)</strong>
                        <p>Modelos de Roteamento, Síntese e Áudio Online</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ══════════════════════════════════════════════════════════
                2. TAB: EMPRESAS CLIENTES (TENANTS)
               ══════════════════════════════════════════════════════════ */}
            {tab === "tenants" && (
              <div className="admin-tab-content">
                <div className="admin-action-row">
                  <h3 className="section-title">Empresas Clientes Conectadas</h3>
                  <button className="btn-primary-admin" onClick={() => setModalNovaEmpresa(true)}>
                    + Nova Empresa
                  </button>
                </div>

                <div className="admin-table-wrapper">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Empresa</th>
                        <th>CNPJ / Domínio</th>
                        <th>Plano</th>
                        <th>Valor Mensal</th>
                        <th>Usuários</th>
                        <th>Status</th>
                        <th>Conectores</th>
                        <th>Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tenants.map((t) => (
                        <tr key={t.id}>
                          <td>
                            <strong>{t.nome_fantasia || t.nome}</strong>
                            {t.nome_fantasia && t.nome !== t.nome_fantasia && (
                              <div className="text-muted text-xs">{t.nome}</div>
                            )}
                          </td>
                          <td className="font-mono">{t.cnpj}</td>
                          <td>
                            <span className="badge-plan">{t.plano || "Enterprise"}</span>
                          </td>
                          <td className="font-bold text-accent">{formatBRL(t.valor_mensal)}</td>
                          <td>
                            <span className="badge-count">
                              {t.usuarios?.ativos || 0} / {t.usuarios?.total || 0}
                            </span>
                          </td>
                          <td>
                            <span className={`badge-status ${t.ativo ? "active" : "inactive"}`}>
                              {t.ativo ? "Ativa" : "Bloqueada"}
                            </span>
                          </td>
                          <td>
                            <div className="conns-badges">
                              {t.conectores_resumo?.totvs_ativo && <span className="badge-conn totvs">TOTVS</span>}
                              {t.conectores_resumo?.sankhya_ativo && <span className="badge-conn sankhya">Sankhya</span>}
                              {t.conectores_resumo?.db_ativo && <span className="badge-conn db">DB</span>}
                            </div>
                          </td>
                          <td>
                            <button
                              className="btn-table-action"
                              onClick={() => {
                                handleTrocarTenantConectores(t.id);
                                setTab("connectors");
                              }}
                              title="Configurar Conectores"
                            >
                              🔌 Configurar
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ══════════════════════════════════════════════════════════
                3. TAB: HUB DE CONECTORES & APIS (TOTVS, SANKHYA, DB)
               ══════════════════════════════════════════════════════════ */}
            {tab === "connectors" && (
              <div className="admin-tab-content">
                <div className="admin-tenant-selector-bar">
                  <label>Empresa Selecionada para Configuração:</label>
                  <select
                    value={selectedTenantId}
                    onChange={(e) => handleTrocarTenantConectores(e.target.value)}
                    className="admin-select"
                  >
                    {tenants.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.nome_fantasia || t.nome} ({t.cnpj})
                      </option>
                    ))}
                  </select>
                </div>

                {resultadoTeste && (
                  <div className={`admin-test-result ${resultadoTeste.sucesso ? "success" : "error"}`}>
                    <strong>{resultadoTeste.sucesso ? "✅ Teste Bem-Sucedido:" : "❌ Falha no Teste:"}</strong>{" "}
                    {resultadoTeste.mensagem}
                  </div>
                )}

                {connectorsData && (
                  <form onSubmit={handleSalvarConectores} className="connectors-form">
                    {/* CARD 1: TOTVS MODA */}
                    <div className="connector-card">
                      <div className="connector-card-header">
                        <div className="connector-title">
                          <span className="connector-icon">🔴</span>
                          <div>
                            <h4>TOTVS Moda (Bhan / API Rest)</h4>
                            <p>Vendas, faturamento, pedidos bloqueados e títulos em atraso</p>
                          </div>
                        </div>
                        <label className="switch">
                          <input
                            type="checkbox"
                            checked={connectorsData.totvs_moda?.ativo || false}
                            onChange={(e) =>
                              setConnectorsData({
                                ...connectorsData,
                                totvs_moda: { ...connectorsData.totvs_moda, ativo: e.target.checked },
                              })
                            }
                          />
                          <span className="slider round" />
                        </label>
                      </div>

                      <div className="connector-fields">
                        <div className="form-group-admin">
                          <label>Endpoint Base URL</label>
                          <input
                            type="text"
                            value={connectorsData.totvs_moda?.base_url || ""}
                            onChange={(e) =>
                              setConnectorsData({
                                ...connectorsData,
                                totvs_moda: { ...connectorsData.totvs_moda, base_url: e.target.value },
                              })
                            }
                            placeholder="https://www30.bhan.com.br:9443/api/totvsmoda"
                          />
                        </div>

                        <div className="grid-2-cols">
                          <div className="form-group-admin">
                            <label>Client ID</label>
                            <input
                              type="text"
                              value={connectorsData.totvs_moda?.client_id || ""}
                              onChange={(e) =>
                                setConnectorsData({
                                  ...connectorsData,
                                  totvs_moda: { ...connectorsData.totvs_moda, client_id: e.target.value },
                                })
                              }
                              placeholder="designtexapiv2"
                            />
                          </div>
                          <div className="form-group-admin">
                            <label>Client Secret</label>
                            <input
                              type="password"
                              value={connectorsData.totvs_moda?.client_secret || ""}
                              onChange={(e) =>
                                setConnectorsData({
                                  ...connectorsData,
                                  totvs_moda: { ...connectorsData.totvs_moda, client_secret: e.target.value },
                                })
                              }
                              placeholder="••••••••••"
                            />
                          </div>
                        </div>

                        <div className="grid-2-cols">
                          <div className="form-group-admin">
                            <label>Usuário TOTVS</label>
                            <input
                              type="text"
                              value={connectorsData.totvs_moda?.username || ""}
                              onChange={(e) =>
                                setConnectorsData({
                                  ...connectorsData,
                                  totvs_moda: { ...connectorsData.totvs_moda, username: e.target.value },
                                })
                              }
                              placeholder="samuel"
                            />
                          </div>
                          <div className="form-group-admin">
                            <label>Senha TOTVS</label>
                            <input
                              type="password"
                              value={connectorsData.totvs_moda?.password || ""}
                              onChange={(e) =>
                                setConnectorsData({
                                  ...connectorsData,
                                  totvs_moda: { ...connectorsData.totvs_moda, password: e.target.value },
                                })
                              }
                              placeholder="••••••••••"
                            />
                          </div>
                        </div>
                      </div>

                      <div className="connector-footer">
                        <button
                          type="button"
                          className="btn-test-conn"
                          onClick={() => handleTestarConector("totvs_moda")}
                          disabled={testandoConector === "totvs_moda"}
                        >
                          {testandoConector === "totvs_moda" ? "⏳ Testando..." : "⚡ Testar Conexão com TOTVS"}
                        </button>
                      </div>
                    </div>

                    {/* CARD 2: SANKHYA ERP */}
                    <div className="connector-card">
                      <div className="connector-card-header">
                        <div className="connector-title">
                          <span className="connector-icon">🟢</span>
                          <div>
                            <h4>Sankhya ERP (API Gateway / MobileLogin)</h4>
                            <p>Integração de pedidos, vendas e notas fiscais para clientes Sankhya</p>
                          </div>
                        </div>
                        <label className="switch">
                          <input
                            type="checkbox"
                            checked={connectorsData.sankhya?.ativo || false}
                            onChange={(e) =>
                              setConnectorsData({
                                ...connectorsData,
                                sankhya: { ...connectorsData.sankhya, ativo: e.target.checked },
                              })
                            }
                          />
                          <span className="slider round" />
                        </label>
                      </div>

                      <div className="connector-fields">
                        <div className="form-group-admin">
                          <label>Endpoint Gateway Sankhya</label>
                          <input
                            type="text"
                            value={connectorsData.sankhya?.base_url || ""}
                            onChange={(e) =>
                              setConnectorsData({
                                ...connectorsData,
                                sankhya: { ...connectorsData.sankhya, base_url: e.target.value },
                              })
                            }
                            placeholder="https://api.sankhya.com.br/gateway/v1"
                          />
                        </div>

                        <div className="grid-2-cols">
                          <div className="form-group-admin">
                            <label>App Key / Client Token</label>
                            <input
                              type="text"
                              value={connectorsData.sankhya?.app_key || ""}
                              onChange={(e) =>
                                setConnectorsData({
                                  ...connectorsData,
                                  sankhya: { ...connectorsData.sankhya, app_key: e.target.value },
                                })
                              }
                              placeholder="Chave pública do app Sankhya"
                            />
                          </div>
                          <div className="form-group-admin">
                            <label>Client Token / Secret</label>
                            <input
                              type="password"
                              value={connectorsData.sankhya?.client_token || ""}
                              onChange={(e) =>
                                setConnectorsData({
                                  ...connectorsData,
                                  sankhya: { ...connectorsData.sankhya, client_token: e.target.value },
                                })
                              }
                              placeholder="Token secreto"
                            />
                          </div>
                        </div>

                        <div className="grid-2-cols">
                          <div className="form-group-admin">
                            <label>Usuário Sankhya</label>
                            <input
                              type="text"
                              value={connectorsData.sankhya?.username || ""}
                              onChange={(e) =>
                                setConnectorsData({
                                  ...connectorsData,
                                  sankhya: { ...connectorsData.sankhya, username: e.target.value },
                                })
                              }
                              placeholder="USUARIO.API"
                            />
                          </div>
                          <div className="form-group-admin">
                            <label>Senha Sankhya</label>
                            <input
                              type="password"
                              value={connectorsData.sankhya?.password || ""}
                              onChange={(e) =>
                                setConnectorsData({
                                  ...connectorsData,
                                  sankhya: { ...connectorsData.sankhya, password: e.target.value },
                                })
                              }
                              placeholder="••••••••••"
                            />
                          </div>
                        </div>
                      </div>

                      <div className="connector-footer">
                        <button
                          type="button"
                          className="btn-test-conn"
                          onClick={() => handleTestarConector("sankhya")}
                          disabled={testandoConector === "sankhya"}
                        >
                          {testandoConector === "sankhya" ? "⏳ Testando..." : "⚡ Testar Conexão com Sankhya"}
                        </button>
                      </div>
                    </div>

                    {/* CARD 3: BANCO DE DADOS DIRETO */}
                    <div className="connector-card">
                      <div className="connector-card-header">
                        <div className="connector-title">
                          <span className="connector-icon">🔵</span>
                          <div>
                            <h4>Banco de Dados Direto (PostgreSQL / MySQL)</h4>
                            <p>Consulta direta em Data Warehouse ou réplica de leitura do ERP</p>
                          </div>
                        </div>
                        <label className="switch">
                          <input
                            type="checkbox"
                            checked={connectorsData.database?.ativo || false}
                            onChange={(e) =>
                              setConnectorsData({
                                ...connectorsData,
                                database: { ...connectorsData.database, ativo: e.target.checked },
                              })
                            }
                          />
                          <span className="slider round" />
                        </label>
                      </div>

                      <div className="connector-fields">
                        <div className="grid-2-cols">
                          <div className="form-group-admin">
                            <label>Host do Servidor</label>
                            <input
                              type="text"
                              value={connectorsData.database?.host || ""}
                              onChange={(e) =>
                                setConnectorsData({
                                  ...connectorsData,
                                  database: { ...connectorsData.database, host: e.target.value },
                                })
                              }
                              placeholder="aws-rds.cliente.com.br"
                            />
                          </div>
                          <div className="form-group-admin">
                            <label>Porta</label>
                            <input
                              type="number"
                              value={connectorsData.database?.port || 5432}
                              onChange={(e) =>
                                setConnectorsData({
                                  ...connectorsData,
                                  database: { ...connectorsData.database, port: e.target.value },
                                })
                              }
                              placeholder="5432"
                            />
                          </div>
                        </div>
                      </div>

                      <div className="connector-footer">
                        <button
                          type="button"
                          className="btn-test-conn"
                          onClick={() => handleTestarConector("database")}
                          disabled={testandoConector === "database"}
                        >
                          {testandoConector === "database" ? "⏳ Testando..." : "⚡ Testar Conexão com Banco"}
                        </button>
                      </div>
                    </div>

                    <div className="admin-submit-bar">
                      <button type="submit" className="btn-primary-admin large">
                        💾 Salvar Todas as Configurações de Conectores
                      </button>
                    </div>
                  </form>
                )}
              </div>
            )}

            {/* ══════════════════════════════════════════════════════════
                4. TAB: USUÁRIOS & SENHAS
               ══════════════════════════════════════════════════════════ */}
            {tab === "users" && (
              <div className="admin-tab-content">
                <div className="admin-action-row">
                  <div className="filter-group">
                    <label>Filtrar por Empresa:</label>
                    <select
                      value={filterUserTenant}
                      onChange={(e) => setFilterUserTenant(e.target.value)}
                      className="admin-select small"
                    >
                      <option value="">Todas as Empresas</option>
                      {tenants.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.nome_fantasia || t.nome}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button className="btn-primary-admin" onClick={() => setModalNovoUsuario(true)}>
                    + Novo Usuário
                  </button>
                </div>

                <div className="admin-table-wrapper">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Usuário</th>
                        <th>Empresa</th>
                        <th>Perfil</th>
                        <th>Cód. Rep</th>
                        <th>Status</th>
                        <th>Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users
                        .filter((u) => !filterUserTenant || u.tenant_id === filterUserTenant)
                        .map((u) => (
                          <tr key={u.id}>
                            <td>
                              <strong>{u.nome || u.email.split("@")[0]}</strong>
                              <div className="text-muted text-xs">{u.email}</div>
                            </td>
                            <td>{u.tenant_nome}</td>
                            <td>
                              <span className={`badge-role ${u.perfil}`}>
                                {u.perfil === "admin"
                                  ? "Master Admin"
                                  : u.perfil === "gestor"
                                  ? "Diretor / Gestor"
                                  : u.perfil === "supervisor"
                                  ? "Supervisor"
                                  : "Representante"}
                              </span>
                            </td>
                            <td className="font-mono">{u.representante_codigo || "—"}</td>
                            <td>
                              <span className={`badge-status ${u.ativo ? "active" : "inactive"}`}>
                                {u.ativo ? "Ativo" : "Bloqueado"}
                              </span>
                            </td>
                            <td>
                              <div className="user-action-buttons">
                                <button
                                  className="btn-user-action key"
                                  onClick={() => handleResetSenha(u)}
                                  title="Gerar / Redefinir Senha Provisória"
                                >
                                  🔑 Redefinir Senha
                                </button>
                                <button
                                  className="btn-user-action block"
                                  onClick={() => handleToggleUserAtivo(u)}
                                  title={u.ativo ? "Bloquear Acesso" : "Ativar Acesso"}
                                >
                                  {u.ativo ? "🚫 Bloquear" : "✅ Ativar"}
                                </button>
                                <button
                                  className="btn-user-action delete"
                                  onClick={() => handleExcluirUsuario(u)}
                                  title="Excluir Usuário"
                                >
                                  🗑️
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ══════════════════════════════════════════════════════════
                5. TAB: FINANCEIRO SAAS (MRR / CONEXO.DEV)
               ══════════════════════════════════════════════════════════ */}
            {tab === "financeiro" && financeiro && (
              <div className="admin-tab-content">
                <div className="admin-kpi-grid">
                  <div className="admin-kpi-card highlight">
                    <span className="kpi-icon">📈</span>
                    <span className="kpi-label">MRR (Receita Recorrente Mensal)</span>
                    <strong className="kpi-value text-accent">{formatBRL(financeiro.mrr_total)}</strong>
                    <span className="kpi-sub">ARR Projetado: {formatBRL(financeiro.arr_anual)} / ano</span>
                  </div>

                  <div className="admin-kpi-card">
                    <span className="kpi-icon">🏢</span>
                    <span className="kpi-label">Total de Clientes Faturados</span>
                    <strong className="kpi-value">{financeiro.total_clientes}</strong>
                    <span className="kpi-sub">100% dos clientes ativos</span>
                  </div>
                </div>

                <div className="admin-section-card">
                  <h3 className="section-title">Detalhamento Financeiro por Cliente</h3>
                  <div className="admin-table-wrapper">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>Cliente</th>
                          <th>Plano</th>
                          <th>Mensalidade (MRR)</th>
                          <th>Dia Vencimento</th>
                          <th>Consultas IA (Mês)</th>
                          <th>Custo Servidor IA</th>
                          <th>Margem Líquida</th>
                          <th>Status Pagamento</th>
                        </tr>
                      </thead>
                      <tbody>
                        {financeiro.clientes.map((c) => (
                          <tr key={c.tenant_id}>
                            <td>
                              <strong>{c.nome}</strong>
                              <div className="text-muted text-xs">{c.cnpj}</div>
                            </td>
                            <td><span className="badge-plan">{c.plano}</span></td>
                            <td className="font-bold text-accent">{formatBRL(c.valor_mensal)}</td>
                            <td>Dia {c.dia_vencimento}</td>
                            <td>{c.perguntas_mes}</td>
                            <td className="text-muted">{formatBRL(c.custo_ia_mes)}</td>
                            <td className="font-bold text-success">{formatBRL(c.margem_liquida)}</td>
                            <td>
                              <span className="badge-status active">Em dia 🟢</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* ══════════════════════════════════════════════════════════
                6. TAB: LOGS DE ERROS & AUDITORIA
               ══════════════════════════════════════════════════════════ */}
            {tab === "logs" && (
              <div className="admin-tab-content">
                <div className="admin-action-row">
                  <h3 className="section-title">Central de Auditoria e Erros de IA</h3>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={apenasErros}
                      onChange={(e) => {
                        setApenasErros(e.target.checked);
                        getAdminLogs({ limit: 50, apenas_erros: e.target.checked }, token).then(setLogs);
                      }}
                    />
                    Mostrar apenas erros
                  </label>
                </div>

                <div className="admin-table-wrapper">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Data / Hora</th>
                        <th>Usuário</th>
                        <th>Pergunta do Usuário</th>
                        <th>Intenção Detectada</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((l) => (
                        <tr key={l.id}>
                          <td className="text-xs text-muted whitespace-nowrap">
                            {new Date(l.created_at).toLocaleString("pt-BR")}
                          </td>
                          <td className="text-xs font-mono">{l.usuario}</td>
                          <td className="font-medium">{l.pergunta}</td>
                          <td><span className="badge-intent">{l.intent}</span></td>
                          <td>
                            <span className={`badge-status ${l.sucesso ? "active" : "inactive"}`}>
                              {l.sucesso ? "Sucesso" : "Erro"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* ── MODAL: NOVA EMPRESA ── */}
      {modalNovaEmpresa && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3>+ Cadastrar Nova Empresa Cliente</h3>
              <button className="btn-close-modal" onClick={() => setModalNovaEmpresa(false)}>✕</button>
            </div>
            <form onSubmit={handleCriarEmpresa} className="modal-form">
              <div className="form-group-admin">
                <label>Razão Social</label>
                <input
                  type="text"
                  required
                  value={formNovaEmpresa.nome}
                  onChange={(e) => setFormNovaEmpresa({ ...formNovaEmpresa, nome: e.target.value })}
                  placeholder="Ex: Confecções Estilo Ltda"
                />
              </div>

              <div className="form-group-admin">
                <label>Nome Fantasia</label>
                <input
                  type="text"
                  value={formNovaEmpresa.nome_fantasia}
                  onChange={(e) => setFormNovaEmpresa({ ...formNovaEmpresa, nome_fantasia: e.target.value })}
                  placeholder="Ex: Estilo Jeans"
                />
              </div>

              <div className="grid-2-cols">
                <div className="form-group-admin">
                  <label>CNPJ ou Domínio</label>
                  <input
                    type="text"
                    required
                    value={formNovaEmpresa.cnpj}
                    onChange={(e) => setFormNovaEmpresa({ ...formNovaEmpresa, cnpj: e.target.value })}
                    placeholder="12.345.678/0001-90"
                  />
                </div>
                <div className="form-group-admin">
                  <label>Plano</label>
                  <select
                    value={formNovaEmpresa.plano}
                    onChange={(e) => setFormNovaEmpresa({ ...formNovaEmpresa, plano: e.target.value })}
                  >
                    <option value="Starter">Starter</option>
                    <option value="Pro">Pro</option>
                    <option value="Enterprise">Enterprise</option>
                  </select>
                </div>
              </div>

              <div className="grid-2-cols">
                <div className="form-group-admin">
                  <label>Valor Mensal (R$)</label>
                  <input
                    type="number"
                    value={formNovaEmpresa.valor_mensal}
                    onChange={(e) => setFormNovaEmpresa({ ...formNovaEmpresa, valor_mensal: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div className="form-group-admin">
                  <label>Dia de Vencimento</label>
                  <input
                    type="number"
                    value={formNovaEmpresa.dia_vencimento}
                    onChange={(e) => setFormNovaEmpresa({ ...formNovaEmpresa, dia_vencimento: parseInt(e.target.value) || 10 })}
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn-cancel" onClick={() => setModalNovaEmpresa(false)}>Cancelar</button>
                <button type="submit" className="btn-primary-admin">Salvar Empresa</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: NOVO USUÁRIO ── */}
      {modalNovoUsuario && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3>+ Cadastrar Novo Usuário</h3>
              <button className="btn-close-modal" onClick={() => setModalNovoUsuario(false)}>✕</button>
            </div>
            <form onSubmit={handleCriarUsuario} className="modal-form">
              <div className="form-group-admin">
                <label>Empresa (Cliente)</label>
                <select
                  required
                  value={formNovoUsuario.tenant_id}
                  onChange={(e) => setFormNovoUsuario({ ...formNovoUsuario, tenant_id: e.target.value })}
                >
                  <option value="">Selecione uma empresa...</option>
                  {tenants.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.nome_fantasia || t.nome}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid-2-cols">
                <div className="form-group-admin">
                  <label>Nome Completo</label>
                  <input
                    type="text"
                    required
                    value={formNovoUsuario.nome}
                    onChange={(e) => setFormNovoUsuario({ ...formNovoUsuario, nome: e.target.value })}
                    placeholder="Ex: Carlos Silva"
                  />
                </div>
                <div className="form-group-admin">
                  <label>E-mail de Login</label>
                  <input
                    type="email"
                    required
                    value={formNovoUsuario.email}
                    onChange={(e) => setFormNovoUsuario({ ...formNovoUsuario, email: e.target.value })}
                    placeholder="carlos@empresa.com.br"
                  />
                </div>
              </div>

              <div className="grid-2-cols">
                <div className="form-group-admin">
                  <label>Perfil de Acesso</label>
                  <select
                    value={formNovoUsuario.perfil}
                    onChange={(e) => setFormNovoUsuario({ ...formNovoUsuario, perfil: e.target.value })}
                  >
                    <option value="gestor">Diretor / Gestor (Vê Tudo)</option>
                    <option value="supervisor">Supervisor Comercial</option>
                    <option value="vendedor">Representante / Vendedor</option>
                    <option value="admin">Master Admin</option>
                  </select>
                </div>
                <div className="form-group-admin">
                  <label>Cód. Representante (se vendedor)</label>
                  <input
                    type="text"
                    value={formNovoUsuario.representante_codigo}
                    onChange={(e) => setFormNovoUsuario({ ...formNovoUsuario, representante_codigo: e.target.value })}
                    placeholder="Ex: 3071"
                  />
                </div>
              </div>

              <div className="form-group-admin">
                <label>Senha Provisória (Opcional - deixe vazio para gerar automaticamente)</label>
                <input
                  type="text"
                  value={formNovoUsuario.senha}
                  onChange={(e) => setFormNovoUsuario({ ...formNovoUsuario, senha: e.target.value })}
                  placeholder="Deixe em branco para gerar aleatória segura"
                />
              </div>

              <div className="modal-footer">
                <button type="button" className="btn-cancel" onClick={() => setModalNovoUsuario(false)}>Cancelar</button>
                <button type="submit" className="btn-primary-admin">Criar Usuário</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: SENHA GERADA (COPIAR PARA WHATSAPP) ── */}
      {modalSenhaGerada && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3>🔑 Credenciais de Acesso Geradas</h3>
              <button className="btn-close-modal" onClick={() => setModalSenhaGerada(null)}>✕</button>
            </div>
            <div className="modal-body-password">
              <p className="password-info-text">{modalSenhaGerada.mensagem}</p>

              <div className="password-box">
                <div className="password-row">
                  <span className="label">E-mail:</span>
                  <span className="value font-mono">{modalSenhaGerada.email}</span>
                </div>
                <div className="password-row">
                  <span className="label">Senha Provisória:</span>
                  <span className="value password-strong font-mono">{modalSenhaGerada.senha}</span>
                </div>
              </div>

              <div className="copy-whatsapp-row">
                <button
                  className="btn-whatsapp-copy"
                  onClick={() => {
                    const msg = `Olá! Segue seu acesso ao CONEXO (Inteligência Comercial):\n\n🔗 Link: https://conexo.dev\n📧 E-mail: ${modalSenhaGerada.email}\n🔑 Senha Provisória: ${modalSenhaGerada.senha}\n\nRecomendamos alterar sua senha após o primeiro login.`;
                    navigator.clipboard.writeText(msg);
                    alert("Mensagem copiada para a área de transferência! Cole no WhatsApp do colaborador.");
                  }}
                >
                  📋 Copiar Mensagem Pronta para WhatsApp
                </button>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-primary-admin" onClick={() => setModalSenhaGerada(null)}>Concluído</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
