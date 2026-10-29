import { useState } from "react";
import { testAdminConnector } from "../api";

export const CATALOGO_SISTEMAS = [
  // Grandes e Médias Empresas
  {
    id: "totvs_protheus",
    categoria: "Grandes e Médias Empresas",
    nome: "TOTVS Protheus",
    subtitulo: "Linha Protheus REST API / Web Services ADVPL",
    icone: "🏭",
    cor: "#0284c7",
    camposPadrao: {
      nome: "TOTVS Protheus",
      tipo: "totvs_protheus",
      ativo: true,
      base_url: "https://erp.cliente.com.br:8084/rest",
      username: "",
      password: "",
      client_id: "",
      client_secret: "",
      company_code: "01",
      branch_code: "01",
      token: "",
    },
    campos: [
      { key: "base_url", label: "Endpoint Base URL (REST) *", placeholder: "https://erp.cliente.com.br:8084/rest", required: true },
      { key: "username", label: "Usuário Protheus *", placeholder: "admin_api", required: true },
      { key: "password", label: "Senha Protheus *", placeholder: "••••••••", type: "password", required: true },
      { key: "company_code", label: "Código da Empresa", placeholder: "01" },
      { key: "branch_code", label: "Código da Filial", placeholder: "01" },
      { key: "token", label: "Bearer Token / Chave API (Opcional)", placeholder: "Token caso autentique via Bearer", type: "password" },
    ],
  },
  {
    id: "totvs_moda",
    categoria: "Grandes e Médias Empresas",
    nome: "TOTVS Moda (Bhan)",
    subtitulo: "Linha Moda Varejo & Atacado Têxtil / Confecção",
    icone: "🧵",
    cor: "#0ea5e9",
    camposPadrao: {
      nome: "TOTVS Moda",
      tipo: "totvs_moda",
      ativo: true,
      base_url: "https://www30.bhan.com.br:9443/api/totvsmoda",
      client_id: "",
      client_secret: "",
      username: "",
      password: "",
      company_code: "01",
      branch_code: "001",
    },
    campos: [
      { key: "base_url", label: "Endpoint Base URL *", placeholder: "https://www30.bhan.com.br:9443/api/totvsmoda", required: true },
      { key: "client_id", label: "Client ID *", placeholder: "designtexapiv2", required: true },
      { key: "client_secret", label: "Client Secret *", placeholder: "••••••••", type: "password", required: true },
      { key: "username", label: "Usuário TOTVS *", placeholder: "samuel", required: true },
      { key: "password", label: "Senha TOTVS *", placeholder: "••••••••", type: "password", required: true },
      { key: "company_code", label: "Código Empresa", placeholder: "01" },
      { key: "branch_code", label: "Código Filial", placeholder: "001" },
    ],
  },
  {
    id: "sankhya",
    categoria: "Grandes e Médias Empresas",
    nome: "Sankhya ERP",
    subtitulo: "Sankhya Gateway API / ServiceInvoker / MobileLoginSP",
    icone: "🟢",
    cor: "#16a34a",
    camposPadrao: {
      nome: "Sankhya ERP",
      tipo: "sankhya",
      ativo: true,
      base_url: "https://api.sankhya.com.br/gateway/v1",
      app_key: "",
      client_token: "",
      username: "",
      password: "",
    },
    campos: [
      { key: "base_url", label: "Endpoint Gateway Sankhya *", placeholder: "https://api.sankhya.com.br/gateway/v1", required: true },
      { key: "app_key", label: "App Key do Gateway", placeholder: "Chave pública do app Sankhya" },
      { key: "client_token", label: "Client Token / Secret", placeholder: "Token secreto", type: "password" },
      { key: "username", label: "Usuário Sankhya *", placeholder: "usuario_api", required: true },
      { key: "password", label: "Senha Sankhya *", placeholder: "••••••••", type: "password", required: true },
    ],
  },
  {
    id: "senior",
    categoria: "Grandes e Médias Empresas",
    nome: "Senior Sistemas",
    subtitulo: "Sapiens ERP / G5 / Gestão Empresarial",
    icone: "🟦",
    cor: "#2563eb",
    camposPadrao: {
      nome: "Senior Sistemas",
      tipo: "senior",
      ativo: true,
      base_url: "https://senior.cliente.com.br:8181/g5-senior-services",
      username: "",
      password: "",
      token: "",
    },
    campos: [
      { key: "base_url", label: "Endpoint Base URL (G5 Services) *", placeholder: "https://senior.cliente.com.br:8181/g5-senior-services", required: true },
      { key: "username", label: "Usuário Senior", placeholder: "senior_api" },
      { key: "password", label: "Senha Senior", placeholder: "••••••••", type: "password" },
      { key: "token", label: "API Token / Chave de Acesso", placeholder: "Token de integração", type: "password" },
    ],
  },
  {
    id: "sap_b1",
    categoria: "Grandes e Médias Empresas",
    nome: "SAP Business One",
    subtitulo: "SAP B1 Service Layer / OData API",
    icone: "🔷",
    cor: "#1d4ed8",
    camposPadrao: {
      nome: "SAP Business One",
      tipo: "sap_b1",
      ativo: true,
      base_url: "https://sap.cliente.com.br:50000/b1s/v1",
      company_db: "",
      username: "",
      password: "",
    },
    campos: [
      { key: "base_url", label: "Service Layer URL *", placeholder: "https://sap.cliente.com.br:50000/b1s/v1", required: true },
      { key: "company_db", label: "Company DB (Banco de Dados SAP) *", placeholder: "SBO_CLIENTE", required: true },
      { key: "username", label: "Usuário B1 *", placeholder: "manager", required: true },
      { key: "password", label: "Senha B1 *", placeholder: "••••••••", type: "password", required: true },
    ],
  },
  {
    id: "oracle_netsuite",
    categoria: "Grandes e Médias Empresas",
    nome: "Oracle NetSuite",
    subtitulo: "Oracle NetSuite Cloud ERP SuiteTalk REST",
    icone: "🔴",
    cor: "#dc2626",
    camposPadrao: {
      nome: "Oracle NetSuite",
      tipo: "oracle_netsuite",
      ativo: true,
      base_url: "https://accountid.suitetalk.api.netsuite.com/services/rest",
      account_id: "",
      consumer_key: "",
      consumer_secret: "",
      token_id: "",
      token_secret: "",
    },
    campos: [
      { key: "base_url", label: "SuiteTalk REST URL *", placeholder: "https://accountid.suitetalk.api.netsuite.com/services/rest", required: true },
      { key: "account_id", label: "Account ID NetSuite", placeholder: "1234567" },
      { key: "consumer_key", label: "Consumer Key", placeholder: "••••••••" },
      { key: "consumer_secret", label: "Consumer Secret", placeholder: "••••••••", type: "password" },
      { key: "token_id", label: "Token ID", placeholder: "••••••••" },
      { key: "token_secret", label: "Token Secret", placeholder: "••••••••", type: "password" },
    ],
  },
  {
    id: "cigam",
    categoria: "Grandes e Médias Empresas",
    nome: "CIGAM ERP",
    subtitulo: "CIGAM WebServices REST",
    icone: "⚙️",
    cor: "#475569",
    camposPadrao: {
      nome: "CIGAM ERP",
      tipo: "cigam",
      ativo: true,
      base_url: "https://cigam.cliente.com.br/api",
      token: "",
      username: "",
      password: "",
    },
    campos: [
      { key: "base_url", label: "Endpoint CIGAM API *", placeholder: "https://cigam.cliente.com.br/api", required: true },
      { key: "token", label: "Token de Autenticação", placeholder: "Token CIGAM", type: "password" },
      { key: "username", label: "Usuário", placeholder: "usuario" },
      { key: "password", label: "Senha", placeholder: "••••••••", type: "password" },
    ],
  },
  {
    id: "linx",
    categoria: "Grandes e Médias Empresas",
    nome: "Linx ERP (Microvix / Core)",
    subtitulo: "Linx ERP Varejo, Lojas e Franquias",
    icone: "🏬",
    cor: "#059669",
    camposPadrao: {
      nome: "Linx ERP",
      tipo: "linx",
      ativo: true,
      base_url: "https://api.linx.com.br",
      token: "",
      cnpj_empresa: "",
    },
    campos: [
      { key: "base_url", label: "Endpoint API Linx *", placeholder: "https://api.linx.com.br", required: true },
      { key: "token", label: "Chave / Token Linx *", placeholder: "Token Linx", type: "password", required: true },
      { key: "cnpj_empresa", label: "CNPJ da Loja/Matriz", placeholder: "00.000.000/0001-00" },
    ],
  },

  // PMEs, Varejo e E-commerce
  {
    id: "omie",
    categoria: "PMEs, Varejo e E-commerce",
    nome: "Omie ERP",
    subtitulo: "API v1 REST Omie (Vendas, Clientes, Estoque e Finanças)",
    icone: "🟠",
    cor: "#ea580c",
    camposPadrao: {
      nome: "Omie ERP",
      tipo: "omie",
      ativo: true,
      app_key: "",
      app_secret: "",
    },
    campos: [
      { key: "app_key", label: "App Key Omie *", placeholder: "Ex: 1234567890123", required: true },
      { key: "app_secret", label: "App Secret Omie *", placeholder: "Ex: a1b2c3d4e5f6g7h8", type: "password", required: true },
    ],
  },
  {
    id: "conta_azul",
    categoria: "PMEs, Varejo e E-commerce",
    nome: "Conta Azul",
    subtitulo: "Conta Azul API v1 / Access Token",
    icone: "🔵",
    cor: "#0284c7",
    camposPadrao: {
      nome: "Conta Azul",
      tipo: "conta_azul",
      ativo: true,
      token: "",
      client_id: "",
      client_secret: "",
    },
    campos: [
      { key: "token", label: "Access Token / Chave de Integração *", placeholder: "Token de acesso API", type: "password", required: true },
      { key: "client_id", label: "Client ID (Opcional)", placeholder: "Client ID OAuth" },
      { key: "client_secret", label: "Client Secret (Opcional)", placeholder: "••••••••", type: "password" },
    ],
  },
  {
    id: "bling",
    categoria: "PMEs, Varejo e E-commerce",
    nome: "Bling ERP",
    subtitulo: "Bling ERP API v3 / Token de Acesso",
    icone: "🟡",
    cor: "#ca8a04",
    camposPadrao: {
      nome: "Bling ERP",
      tipo: "bling",
      ativo: true,
      api_token: "",
    },
    campos: [
      { key: "api_token", label: "API Key / Access Token Bling v3 *", placeholder: "Token de API do Bling", type: "password", required: true },
    ],
  },
  {
    id: "tiny",
    categoria: "PMEs, Varejo e E-commerce",
    nome: "Tiny ERP",
    subtitulo: "Tiny ERP API v2/v3 Token",
    icone: "🟢",
    cor: "#10b981",
    camposPadrao: {
      nome: "Tiny ERP",
      tipo: "tiny",
      ativo: true,
      token: "",
    },
    campos: [
      { key: "token", label: "Token da API Tiny *", placeholder: "Token de integração Tiny", type: "password", required: true },
    ],
  },

  // Bancos de Dados & Webhooks
  {
    id: "database",
    categoria: "Bancos de Dados & Webhooks",
    nome: "PostgreSQL / Supabase",
    subtitulo: "Conexão direta SQL PostgreSQL ou Supabase",
    icone: "🐘",
    cor: "#336791",
    camposPadrao: {
      nome: "PostgreSQL (Supabase)",
      tipo: "postgresql",
      ativo: true,
      host: "liolnupwhhpsryfgnnyl.supabase.co",
      port: 5432,
      database: "postgres",
      username: "postgres",
      password: "",
      schema: "public",
    },
    campos: [
      { key: "host", label: "Host do Servidor *", placeholder: "db.cliente.com.br ou supabase.co", required: true },
      { key: "port", label: "Porta *", placeholder: "5432", type: "number", required: true },
      { key: "database", label: "Nome do Banco de Dados *", placeholder: "postgres", required: true },
      { key: "username", label: "Usuário do Banco *", placeholder: "postgres", required: true },
      { key: "password", label: "Senha do Banco *", placeholder: "••••••••", type: "password", required: true },
      { key: "schema", label: "Schema", placeholder: "public" },
    ],
  },
  {
    id: "mysql",
    categoria: "Bancos de Dados & Webhooks",
    nome: "MySQL / MariaDB",
    subtitulo: "Conexão direta SQL MySQL ou MariaDB",
    icone: "🐬",
    cor: "#00758f",
    camposPadrao: {
      nome: "MySQL",
      tipo: "mysql",
      ativo: true,
      host: "",
      port: 3306,
      database: "",
      username: "",
      password: "",
    },
    campos: [
      { key: "host", label: "Host MySQL *", placeholder: "mysql.cliente.com.br", required: true },
      { key: "port", label: "Porta *", placeholder: "3306", type: "number", required: true },
      { key: "database", label: "Banco de Dados *", placeholder: "banco_erp", required: true },
      { key: "username", label: "Usuário *", placeholder: "root", required: true },
      { key: "password", label: "Senha *", placeholder: "••••••••", type: "password", required: true },
    ],
  },
  {
    id: "sqlserver",
    categoria: "Bancos de Dados & Webhooks",
    nome: "Microsoft SQL Server",
    subtitulo: "Conexão direta T-SQL Microsoft SQL Server",
    icone: "🗄️",
    cor: "#b91c1c",
    camposPadrao: {
      nome: "SQL Server",
      tipo: "sqlserver",
      ativo: true,
      host: "",
      port: 1433,
      database: "",
      username: "",
      password: "",
    },
    campos: [
      { key: "host", label: "Host SQL Server *", placeholder: "sql.cliente.com.br", required: true },
      { key: "port", label: "Porta *", placeholder: "1433", type: "number", required: true },
      { key: "database", label: "Database *", placeholder: "ERP_PRODUCAO", required: true },
      { key: "username", label: "Usuário *", placeholder: "sa", required: true },
      { key: "password", label: "Senha *", placeholder: "••••••••", type: "password", required: true },
    ],
  },
  {
    id: "generic_rest",
    categoria: "Bancos de Dados & Webhooks",
    nome: "API REST Genérica / Webhook",
    subtitulo: "Qualquer sistema próprio ou API REST customizada",
    icone: "🌐",
    cor: "#64748b",
    camposPadrao: {
      nome: "API REST Personalizada",
      tipo: "generic_rest",
      ativo: true,
      base_url: "",
      auth_type: "Bearer",
      auth_token: "",
      header_name: "Authorization",
    },
    campos: [
      { key: "base_url", label: "URL Base da API / Webhook *", placeholder: "https://api.empresa.com.br/v1", required: true },
      { key: "header_name", label: "Nome do Header de Autenticação", placeholder: "Authorization ou X-API-Key" },
      { key: "auth_token", label: "Token / Chave de Acesso", placeholder: "Token ou chave secreta", type: "password" },
    ],
  },
];

export default function AddConnectorModal({ token, tenantNome, onSalvar, onClose }) {
  const [etapa, setEtapa] = useState("busca"); // busca | config
  const [busca, setBusca] = useState("");
  const [sistemaSel, setSistemaSel] = useState(null);
  const [formData, setFormData] = useState({});
  const [apelidoConector, setApelidoConector] = useState("");
  const [chaveConector, setChaveConector] = useState("");
  const [testando, setTestando] = useState(false);
  const [resultadoTeste, setResultadoTeste] = useState(null);

  // Filtragem dos sistemas em tempo real
  const buscaLimpa = busca.trim().toLowerCase();
  const sistemasFiltrados = CATALOGO_SISTEMAS.filter(
    (s) =>
      s.nome.toLowerCase().includes(buscaLimpa) ||
      s.subtitulo.toLowerCase().includes(buscaLimpa) ||
      s.categoria.toLowerCase().includes(buscaLimpa) ||
      s.id.toLowerCase().includes(buscaLimpa)
  );

  const categorias = Array.from(new Set(sistemasFiltrados.map((s) => s.categoria)));

  function handleSelecionarSistema(sis) {
    setSistemaSel(sis);
    setApelidoConector(sis.nome);
    // Cria chave única (ex: omie_1, totvs_moda_matriz)
    const chaveSugestao = `${sis.id}_${Date.now().toString().slice(-4)}`;
    setChaveConector(chaveSugestao);
    setFormData({ ...sis.camposPadrao });
    setResultadoTeste(null);
    setEtapa("config");
  }

  async function handleTestarConexao() {
    setTestando(true);
    setResultadoTeste(null);
    try {
      const res = await testAdminConnector(sistemaSel.id, formData, token);
      setResultadoTeste(res);
    } catch (e) {
      setResultadoTeste({ sucesso: false, mensagem: e.message || "Erro de conexão." });
    } finally {
      setTestando(false);
    }
  }

  function handleSalvar(e) {
    e.preventDefault();
    if (!chaveConector.trim()) return;

    const conectorFinal = {
      ...formData,
      nome: apelidoConector.trim() || sistemaSel.nome,
      tipo: sistemaSel.id,
      icone: sistemaSel.icone,
      ativo: formData.ativo !== false,
      adicionado_em: new Date().toISOString(),
    };

    onSalvar(chaveConector.trim(), conectorFinal);
    onClose();
  }

  return (
    <div className="admin-modal-backdrop" onClick={onClose}>
      <div className="admin-modal-card" style={{ maxWidth: "880px", width: "95%" }} onClick={(e) => e.stopPropagation()}>
        <div className="admin-modal-header">
          <div>
            <h3>
              {etapa === "busca" ? "🔌 Adicionar Novo Sistema / ERP" : `⚙️ Configurar ${sistemaSel?.nome}`}
            </h3>
            <p className="modal-subtitle">
              Empresa Contratante: <strong>{tenantNome}</strong>
            </p>
          </div>
          <button className="admin-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="admin-modal-body" style={{ maxHeight: "72vh", overflowY: "auto" }}>
          {/* ── ETAPA 1: BUSCA E SELEÇÃO DO SISTEMA ── */}
          {etapa === "busca" && (
            <div>
              <div className="system-search-bar">
                <span className="system-search-icon">🔍</span>
                <input
                  type="text"
                  autoFocus
                  className="system-search-input"
                  placeholder="Comece a digitar o nome do sistema (ex: Omie, TOTVS, Senior, Bling, Sankhya, SAP, Conta Azul, Oracle...)"
                  value={busca}
                  onChange={(e) => setBusca(e.target.value)}
                />
              </div>

              {sistemasFiltrados.length === 0 ? (
                <div style={{ textAlign: "center", padding: "40px", color: "#94a3b8" }}>
                  Nenhum sistema encontrado com "<strong>{busca}</strong>".
                  <p style={{ marginTop: "10px", fontSize: "13px" }}>
                    Você pode escolher <strong>API REST Genérica / Webhook</strong> para integrar qualquer sistema proprietário.
                  </p>
                </div>
              ) : (
                categorias.map((cat) => {
                  const items = sistemasFiltrados.filter((s) => s.categoria === cat);
                  if (items.length === 0) return null;
                  return (
                    <div key={cat} className="system-category-section">
                      <div className="system-category-title">{cat}</div>
                      <div className="system-catalog-grid">
                        {items.map((sis) => (
                          <div
                            key={sis.id}
                            className="system-catalog-card"
                            onClick={() => handleSelecionarSistema(sis)}
                          >
                            <div className="system-card-top">
                              <span className="system-card-icon">{sis.icone}</span>
                              <div>
                                <span className="system-card-name">{sis.nome}</span>
                              </div>
                            </div>
                            <span className="system-card-sub">{sis.subtitulo}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}

          {/* ── ETAPA 2: CONFIGURAÇÃO DE CHAVES E SENHAS ── */}
          {etapa === "config" && sistemaSel && (
            <form onSubmit={handleSalvar} className="connectors-form">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <button
                  type="button"
                  className="btn-admin-action"
                  onClick={() => setEtapa("busca")}
                  style={{ background: "rgba(255,255,255,0.08)", color: "#f8fafc", padding: "6px 12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.15)", cursor: "pointer", fontSize: "13px" }}
                >
                  ← Escolher outro sistema
                </button>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "13px", color: "#94a3b8" }}>Conector Ativo:</span>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={formData.ativo !== false}
                      onChange={(e) => setFormData({ ...formData, ativo: e.target.checked })}
                    />
                    <span className="slider round" />
                  </label>
                </div>
              </div>

              <div className="grid-2-cols">
                <div className="form-group-admin">
                  <label>Apelido / Nome da Conexão *</label>
                  <input
                    type="text"
                    value={apelidoConector}
                    onChange={(e) => setApelidoConector(e.target.value)}
                    placeholder="Ex: Omie Loja 2, TOTVS Produção, Sankhya SP"
                    required
                  />
                </div>

                <div className="form-group-admin">
                  <label>Chave de Identificação do Conector *</label>
                  <input
                    type="text"
                    value={chaveConector}
                    onChange={(e) => setChaveConector(e.target.value)}
                    placeholder="ex: omie_loja2, totvs_matriz"
                    required
                  />
                </div>
              </div>

              {/* Campos dinâmicos específicos do sistema escolhido */}
              <div className="connector-fields" style={{ marginTop: "14px" }}>
                {sistemaSel.campos.map((campo) => (
                  <div key={campo.key} className="form-group-admin" style={{ marginBottom: "14px" }}>
                    <label>{campo.label}</label>
                    <input
                      type={campo.type || "text"}
                      value={formData[campo.key] || ""}
                      onChange={(e) => setFormData({ ...formData, [campo.key]: e.target.value })}
                      placeholder={campo.placeholder}
                      required={campo.required}
                    />
                  </div>
                ))}
              </div>

              {resultadoTeste && (
                <div className={`admin-test-result ${resultadoTeste.sucesso ? "success" : "error"}`} style={{ marginTop: "14px" }}>
                  <strong>{resultadoTeste.sucesso ? "✅ Teste Bem-Sucedido:" : "❌ Falha no Teste:"}</strong>{" "}
                  {resultadoTeste.mensagem}
                </div>
              )}

              <div className="modal-actions-right" style={{ display: "flex", justifyContent: "space-between", marginTop: "24px" }}>
                <button
                  type="button"
                  className="btn-conn-action test"
                  style={{ padding: "10px 18px", fontSize: "13px" }}
                  onClick={handleTestarConexao}
                  disabled={testando}
                >
                  {testando ? "⏳ Testando Conexão..." : `⚡ Testar Conexão com ${sistemaSel.nome}`}
                </button>

                <div style={{ display: "flex", gap: "10px" }}>
                  <button type="button" className="btn-admin-cancel" onClick={onClose}>
                    Cancelar
                  </button>
                  <button type="submit" className="btn-primary-admin">
                    💾 Salvar e Ativar Conector
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
