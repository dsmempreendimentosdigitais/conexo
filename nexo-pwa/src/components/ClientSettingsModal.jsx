import { useState, useEffect } from "react";
import { getMinhaEmpresa, abrirSuporte, alterarMinhaSenha } from "../api";

export default function ClientSettingsModal({ token, onClose }) {
  const [tab, setTab] = useState("plano"); // plano | senha | suporte
  const [loading, setLoading] = useState(true);
  const [empresa, setEmpresa] = useState(null);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");

  // Formulário de Senha
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmaSenha, setConfirmaSenha] = useState("");
  const [salvandoSenha, setSalvandoSenha] = useState(false);

  // Formulário de Suporte
  const [chamadoAssunto, setChamadoAssunto] = useState("");
  const [chamadoCategoria, setChamadoCategoria] = useState("Dúvida Comercial");
  const [chamadoMensagem, setChamadoMensagem] = useState("");
  const [enviandoChamado, setEnviandoChamado] = useState(false);
  const [protocoloGerado, setProtocoloGerado] = useState(null);

  useEffect(() => {
    carregarDados();
  }, [token]);

  async function carregarDados() {
    setLoading(true);
    setErro("");
    try {
      const data = await getMinhaEmpresa(token);
      setEmpresa(data);
    } catch (e) {
      setErro(e.message || "Não foi possível carregar as informações da empresa.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSalvarSenha(e) {
    e.preventDefault();
    setErro("");
    setSucesso("");
    if (novaSenha.length < 6) {
      setErro("A nova senha deve ter no mínimo 6 caracteres.");
      return;
    }
    if (novaSenha !== confirmaSenha) {
      setErro("As senhas digitadas não coincidem.");
      return;
    }

    setSalvandoSenha(true);
    try {
      await alterarMinhaSenha(novaSenha, token);
      setSucesso("Senha alterada com sucesso! Utilize a nova senha no próximo acesso.");
      setNovaSenha("");
      setConfirmaSenha("");
      setTimeout(() => setSucesso(""), 4000);
    } catch (e) {
      setErro("Erro ao alterar senha: " + e.message);
    } finally {
      setSalvandoSenha(false);
    }
  }

  async function handleEnviarChamado(e) {
    e.preventDefault();
    setErro("");
    setSucesso("");
    if (!chamadoAssunto.trim() || !chamadoMensagem.trim()) {
      setErro("Preencha o assunto e a mensagem do chamado.");
      return;
    }

    setEnviandoChamado(true);
    try {
      const res = await abrirSuporte(
        {
          assunto: chamadoAssunto.trim(),
          categoria: chamadoCategoria,
          mensagem: chamadoMensagem.trim(),
        },
        token
      );
      setProtocoloGerado(res.protocolo);
      setSucesso(res.mensagem || "Chamado aberto com sucesso!");
      setChamadoAssunto("");
      setChamadoMensagem("");
    } catch (e) {
      setErro("Erro ao enviar chamado: " + e.message);
    } finally {
      setEnviandoChamado(false);
    }
  }

  const msgWhatsApp = encodeURIComponent(
    `Olá equipe de Suporte CONEXO / DSM Empreendimentos Digitais! Sou gestor da empresa ${empresa?.nome_fantasia || empresa?.nome || "cliente"} e gostaria de atendimento sobre minha assinatura.`
  );
  const linkWhatsApp = `https://wa.me/5511999999999?text=${msgWhatsApp}`;

  return (
    <div className="admin-modal-backdrop" onClick={onClose}>
      <div className="admin-modal-card client-settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="admin-modal-header">
          <div>
            <h3>⚙️ Configurações da Empresa & Assinatura</h3>
            <p className="modal-subtitle">
              {empresa?.nome_fantasia || empresa?.nome || "Painel do Cliente"} — CONEXO.dev
            </p>
          </div>
          <button className="admin-modal-close" onClick={onClose}>✕</button>
        </div>

        {/* Abas */}
        <div className="client-settings-tabs">
          <button
            className={`client-tab-btn ${tab === "plano" ? "active" : ""}`}
            onClick={() => { setTab("plano"); setErro(""); setSucesso(""); }}
          >
            💳 Plano & Assinatura
          </button>
          <button
            className={`client-tab-btn ${tab === "senha" ? "active" : ""}`}
            onClick={() => { setTab("senha"); setErro(""); setSucesso(""); }}
          >
            🔒 Alterar Senha
          </button>
          <button
            className={`client-tab-btn ${tab === "suporte" ? "active" : ""}`}
            onClick={() => { setTab("suporte"); setErro(""); setSucesso(""); }}
          >
            🎧 Solicitar Suporte
          </button>
        </div>

        {erro && <div className="admin-banner-erro" style={{ margin: "16px 24px 0" }}>⚠️ {erro}</div>}
        {sucesso && <div className="admin-banner-sucesso" style={{ margin: "16px 24px 0" }}>✅ {sucesso}</div>}

        <div className="admin-modal-body" style={{ maxHeight: "70vh", overflowY: "auto" }}>
          {loading ? (
            <div style={{ padding: "40px", textAlign: "center", color: "#94a3b8" }}>
              Carregando dados da assinatura...
            </div>
          ) : (
            <>
              {/* ── ABA 1: PLANO & ASSINATURA ── */}
              {tab === "plano" && (
                <div className="client-settings-plan-view">
                  <div className="plan-hero-card">
                    <div className="plan-hero-header">
                      <div>
                        <span className="plan-badge-tag">{empresa?.plano || "Enterprise"}</span>
                        <h4 className="plan-company-title">{empresa?.nome_fantasia || empresa?.nome}</h4>
                        <span className="plan-cnpj">CNPJ / Domínio: {empresa?.cnpj || "-"}</span>
                      </div>
                      <div className="plan-price-block">
                        <span className="plan-price-val">
                          R$ {(empresa?.valor_mensal || 3500).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </span>
                        <span className="plan-price-sub">/ mês</span>
                        <div className="plan-status-pill online">
                          ● Assinatura {empresa?.status_pagamento === "em_dia" ? "Ativa & Em Dia" : "Ativa"}
                        </div>
                      </div>
                    </div>

                    <div className="plan-specs-grid">
                      <div className="plan-spec-item">
                        <span className="spec-label">Dia de Vencimento</span>
                        <span className="spec-val">Todo dia {empresa?.dia_vencimento || 10}</span>
                      </div>
                      <div className="plan-spec-item">
                        <span className="spec-label">Usuários na Empresa</span>
                        <span className="spec-val">{empresa?.total_usuarios || 1} ativos</span>
                      </div>
                      <div className="plan-spec-item">
                        <span className="spec-label">Sistemas / ERPs Conectados</span>
                        <span className="spec-val">{empresa?.total_conectores_ativos || 1} ativos</span>
                      </div>
                      <div className="plan-spec-item">
                        <span className="spec-label">IA Comercial CONEXO</span>
                        <span className="spec-val highlight">Ilimitada & 24/7</span>
                      </div>
                    </div>
                  </div>

                  {/* Informações Contratuais */}
                  <div className="contract-summary-card">
                    <h5>📜 Contrato de Prestação de Serviços de Software (SaaS)</h5>
                    <div className="contract-details-grid">
                      <div>
                        <strong>Contratada:</strong>{" "}
                        {empresa?.contrato?.contratada_razao || "DSM Empreendimentos Digitais Ltda"}
                      </div>
                      <div>
                        <strong>Produto:</strong> {empresa?.contrato?.produto || "CONEXO.dev"}
                      </div>
                      <div>
                        <strong>Nº do Contrato:</strong>{" "}
                        {empresa?.contrato?.numero_contrato || "DSM-CNX-2026/001"}
                      </div>
                      <div>
                        <strong>Data de Início:</strong>{" "}
                        {empresa?.contrato?.data_inicio ? new Date(empresa.contrato.data_inicio).toLocaleDateString("pt-BR") : "01/08/2026"}
                      </div>
                      <div>
                        <strong>Vigência:</strong> {empresa?.contrato?.vigencia_meses || 12} meses (Renovação Automática)
                      </div>
                      <div>
                        <strong>SLA de Disponibilidade:</strong> {empresa?.contrato?.sla_garantido || "99.5%"}
                      </div>
                    </div>
                    <p className="contract-lgpd-note">
                      🔒 <strong>Segurança e Sigilo Empresarial:</strong> Todos os dados processados pelo CONEXO são
                      criptografados e de propriedade exclusiva da contratante, em conformidade com as diretrizes da LGPD.
                    </p>
                  </div>
                </div>
              )}

              {/* ── ABA 2: ALTERAR SENHA ── */}
              {tab === "senha" && (
                <form onSubmit={handleSalvarSenha} className="client-settings-form">
                  <div className="form-info-tip">
                    ℹ️ Por segurança, sua senha deve ter no mínimo 6 caracteres. Após a alteração, a nova senha passa a valer imediatamente.
                  </div>

                  <div className="form-group-admin">
                    <label>E-mail do Usuário</label>
                    <input type="text" value={empresa?.usuario_logado?.email || ""} disabled className="input-disabled" />
                  </div>

                  <div className="form-group-admin">
                    <label>Nova Senha *</label>
                    <input
                      type="password"
                      value={novaSenha}
                      onChange={(e) => setNovaSenha(e.target.value)}
                      placeholder="Digite a nova senha (mínimo 6 caracteres)"
                      required
                    />
                  </div>

                  <div className="form-group-admin">
                    <label>Confirmar Nova Senha *</label>
                    <input
                      type="password"
                      value={confirmaSenha}
                      onChange={(e) => setConfirmaSenha(e.target.value)}
                      placeholder="Repita a nova senha exatamente igual"
                      required
                    />
                  </div>

                  <div className="modal-actions-right">
                    <button type="submit" className="btn-primary-admin" disabled={salvandoSenha}>
                      {salvandoSenha ? "Salvando Nova Senha..." : "🔒 Salvar Nova Senha"}
                    </button>
                  </div>
                </form>
              )}

              {/* ── ABA 3: SOLICITAR SUPORTE ── */}
              {tab === "suporte" && (
                <div className="client-support-view">
                  {/* WhatsApp Direto */}
                  <div className="support-whatsapp-card">
                    <div className="support-wa-info">
                      <span className="wa-icon">💬</span>
                      <div>
                        <h4>Atendimento Rápido via WhatsApp</h4>
                        <p>Fale diretamente com nossa equipe técnica de suporte DSM / CONEXO em horário comercial.</p>
                      </div>
                    </div>
                    <a
                      href={linkWhatsApp}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-whatsapp-direct"
                    >
                      Abrir WhatsApp do Suporte
                    </a>
                  </div>

                  {/* Abertura de Chamado */}
                  <div className="support-ticket-card">
                    <h5>📋 Abrir Chamado Técnico / Solicitação Formal</h5>
                    <form onSubmit={handleEnviarChamado}>
                      <div className="grid-2-cols">
                        <div className="form-group-admin">
                          <label>Categoria do Chamado</label>
                          <select
                            value={chamadoCategoria}
                            onChange={(e) => setChamadoCategoria(e.target.value)}
                          >
                            <option value="Dúvida Comercial">Dúvida sobre Consultas / Dados Comerciais</option>
                            <option value="Erro ou Divergência">Erro ou Divergência de Pedidos/Estoque</option>
                            <option value="Conector ERP">Integração ou Conector de ERP (TOTVS/Sankhya)</option>
                            <option value="Usuários e Acessos">Gestão de Usuários e Permissões</option>
                            <option value="Financeiro / Assinatura">Faturamento / Financeiro do Plano</option>
                            <option value="Melhoria ou Sugestão">Sugestão de Novo Recurso</option>
                          </select>
                        </div>

                        <div className="form-group-admin">
                          <label>Assunto Resumido *</label>
                          <input
                            type="text"
                            value={chamadoAssunto}
                            onChange={(e) => setChamadoAssunto(e.target.value)}
                            placeholder="Ex: Divergência na contagem de pedidos de ontem"
                            required
                          />
                        </div>
                      </div>

                      <div className="form-group-admin">
                        <label>Descrição Detalhada *</label>
                        <textarea
                          rows={4}
                          value={chamadoMensagem}
                          onChange={(e) => setChamadoMensagem(e.target.value)}
                          placeholder="Descreva com detalhes o que você precisa ou o comportamento observado..."
                          required
                        />
                      </div>

                      <div className="modal-actions-right">
                        <button type="submit" className="btn-primary-admin" disabled={enviandoChamado}>
                          {enviandoChamado ? "Enviando Chamado..." : "✉️ Enviar Solicitação de Suporte"}
                        </button>
                      </div>
                    </form>

                    {protocoloGerado && (
                      <div className="protocolo-badge-box">
                        📌 <strong>Chamado registrado com sucesso:</strong> Protocolo <code>{protocoloGerado}</code>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
