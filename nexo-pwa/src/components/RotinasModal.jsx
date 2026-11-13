import { useState, useEffect } from "react";
import {
  getRotinasAutomaticas,
  salvarRotinasAutomaticas,
  getEquipeDestinatarios,
  salvarEmailsInternos,
  dispararAvisoEquipe,
  dispararRotinaAgora,
  atualizarRepresentanteEmail
} from "../api";

export default function RotinasModal({ token, onClose }) {
  const [tab, setTab] = useState("rotinas"); // rotinas | aviso | equipe
  const [loading, setLoading] = useState(true);
  const [rotinas, setRotinas] = useState([]);
  const [emailsInternos, setEmailsInternos] = useState([]);
  const [representantes, setRepresentantes] = useState([]);
  const [stats, setStats] = useState({ total_reps_ativos: 0, reps_com_email: 0, reps_sem_email: 0, total_internos: 0 });
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");
  const [disparandoRotinaId, setDisparandoRotinaId] = useState(null);

  // Estado para Seleção Múltipla de Representantes e Supervisor nos Relatórios dos Ciclos
  const [repsSelecionados, setRepsSelecionados] = useState([]);
  const [filtroSupervisor, setFiltroSupervisor] = useState("todos");
  const [modalSelecaoReps, setModalSelecaoReps] = useState(false);
  const [buscaModalReps, setBuscaModalReps] = useState("");

  // Estado para Criar/Editar Rotina
  const [modalEdicaoRotina, setModalEdicaoRotina] = useState(false);
  const [rotinaEmEdicao, setRotinaEmEdicao] = useState(null);
  const [formRotina, setFormRotina] = useState({
    id: "",
    titulo: "",
    descricao: "",
    frequencia: "diario",
    horario: "08:00",
    dias_semana: ["seg", "ter", "qua", "qui", "sex"],
    canal: "email",
    destinatarios_tipo: "equipe_vendas",
    ativo: true,
    mensagem_template: "",
  });

  // Estado para Disparo de Aviso Imediato
  const [avisoAssunto, setAvisoAssunto] = useState("");
  const [avisoMensagem, setAvisoMensagem] = useState("");
  const [avisoPublico, setAvisoPublico] = useState("equipe_vendas");
  const [avisoPrioridade, setAvisoPrioridade] = useState("normal");
  const [avisoExtras, setAvisoExtras] = useState("");
  const [disparandoAviso, setDisparandoAviso] = useState(false);

  // Estado para Gerenciamento de E-mails Internos
  const [novoEmailInterno, setNovoEmailInterno] = useState("");
  const [salvandoInternos, setSalvandoInternos] = useState(false);

  // Estado para Edição de E-mail de Representante
  const [repEmEdicao, setRepEmEdicao] = useState(null);
  const [formRepEmail, setFormRepEmail] = useState("");
  const [formRepTelefone, setFormRepTelefone] = useState("");
  const [salvandoRep, setSalvandoRep] = useState(false);

  // Busca na lista de representantes
  const [buscaRep, setBuscaRep] = useState("");

  useEffect(() => {
    carregarDados();
  }, [token]);

  async function carregarDados() {
    setLoading(true);
    setErro("");
    try {
      const [resRotinas, resEquipe] = await Promise.all([
        getRotinasAutomaticas(token),
        getEquipeDestinatarios(token)
      ]);
      setRotinas(resRotinas.rotinas || []);
      setEmailsInternos(resRotinas.emails_internos || []);
      setStats(resRotinas.stats || {});
      setRepresentantes(resEquipe.representantes || []);
    } catch (e) {
      setErro(e.message || "Erro ao carregar dados das rotinas.");
    } finally {
      setLoading(false);
    }
  }

  // Alternar Status Ativo/Inativo de uma rotina
  async function handleToggleAtivo(rotinaId) {
    const novas = rotinas.map(r => r.id === rotinaId ? { ...r, ativo: !r.ativo } : r);
    setRotinas(novas);
    try {
      await salvarRotinasAutomaticas(novas, token);
      const alterada = novas.find(r => r.id === rotinaId);
      setSucesso(`Rotina "${alterada.titulo}" ${alterada.ativo ? "ativada" : "desativada"} com sucesso!`);
      setTimeout(() => setSucesso(""), 3500);
    } catch (e) {
      setErro("Erro ao salvar alteração: " + e.message);
    }
  }

  // Deletar rotina
  async function handleDeletarRotina(rotinaId) {
    if (!confirm("Tem certeza que deseja remover esta rotina automática?")) return;
    const novas = rotinas.filter(r => r.id !== rotinaId);
    setRotinas(novas);
    try {
      await salvarRotinasAutomaticas(novas, token);
      setSucesso("Rotina removida com sucesso!");
      setTimeout(() => setSucesso(""), 3500);
    } catch (e) {
      setErro("Erro ao excluir rotina: " + e.message);
    }
  }

  // Abrir Modal de Criação ou Edição
  function handleAbrirCriar() {
    setRotinaEmEdicao(null);
    setFormRotina({
      id: "rotina-" + Date.now(),
      titulo: "",
      descricao: "",
      frequencia: "diario",
      horario: "08:00",
      dias_semana: ["seg", "ter", "qua", "qui", "sex"],
      canal: "email",
      destinatarios_tipo: "equipe_vendas",
      ativo: true,
      mensagem_template: "",
    });
    setModalEdicaoRotina(true);
  }

  function handleAbrirEditar(rotina) {
    setRotinaEmEdicao(rotina.id);
    setFormRotina({ ...rotina });
    setModalEdicaoRotina(true);
  }

  async function handleSalvarRotina(e) {
    e.preventDefault();
    if (!formRotina.titulo.trim()) {
      alert("Por favor, preencha o título da rotina.");
      return;
    }

    let novas;
    if (rotinaEmEdicao) {
      novas = rotinas.map(r => r.id === rotinaEmEdicao ? { ...formRotina } : r);
    } else {
      novas = [...rotinas, { ...formRotina, id: formRotina.id || "rotina-" + Date.now() }];
    }

    setRotinas(novas);
    setModalEdicaoRotina(false);
    try {
      await salvarRotinasAutomaticas(novas, token);
      setSucesso(`Rotina "${formRotina.titulo}" salva com sucesso!`);
      setTimeout(() => setSucesso(""), 3500);
    } catch (e) {
      setErro("Erro ao salvar rotina: " + e.message);
    }
  }

  // Disparo Imediato sob Demanda de uma Rotina ("Enviar Agora")
  async function handleDispararRotinaAgora(rotina) {
    const publicoNome = rotina.destinatarios_tipo === "equipe_vendas"
      ? "a Equipe de Vendas (Representantes)"
      : rotina.destinatarios_tipo === "gestao"
      ? "a Gestão / Diretoria"
      : rotina.destinatarios_tipo === "equipe_interna"
      ? "a Equipe Interna"
      : "toda a equipe";

    let contextoAlvo = `consolidado geral (${publicoNome})`;
    if (repsSelecionados.length === 1) {
      const repAlvoObj = representantes.find(r => String(r.codigo) === String(repsSelecionados[0]));
      contextoAlvo = repAlvoObj
        ? `específico para a carteira de #${repAlvoObj.codigo} - ${repAlvoObj.nome}`
        : `para o representante #${repsSelecionados[0]}`;
    } else if (repsSelecionados.length > 1) {
      contextoAlvo = `com ${repsSelecionados.length} relatórios individualizados (1 por representante selecionado)`;
    }

    if (!confirm(`Deseja processar a IA e enviar a rotina "${rotina.titulo}" AGORA ${contextoAlvo}?\n\n(Obs: O envio está seguro em modo homologação e chegará na sua caixa samuel.mc85@gmail.com)`)) {
      return;
    }

    setDisparandoRotinaId(rotina.id);
    setErro("");
    setSucesso("");
    try {
      const res = await dispararRotinaAgora(
        rotina,
        repsSelecionados.length > 0 ? repsSelecionados : null,
        token
      );
      setSucesso(res.mensagem || `Rotina "${rotina.titulo}" enviada agora com sucesso!`);
      if (res.ultima_execucao) {
        setRotinas(prev => prev.map(r => r.id === rotina.id ? { ...r, ultima_execucao: res.ultima_execucao } : r));
      }
      setTimeout(() => setSucesso(""), 7000);
    } catch (err) {
      setErro("Erro ao enviar rotina agora: " + err.message);
    } finally {
      setDisparandoRotinaId(null);
    }
  }

  // Disparo Imediato de Aviso
  async function handleDispararAviso(e) {
    e.preventDefault();
    if (!avisoAssunto.trim() || !avisoMensagem.trim()) {
      setErro("Preencha o assunto e a mensagem do aviso.");
      return;
    }

    const confirmMsg = avisoPublico === "equipe_vendas"
      ? `Disparar este aviso para todos os ${stats.reps_com_email || 65} representantes com e-mail cadastrado?`
      : avisoPublico === "equipe_interna"
      ? `Disparar este aviso para a equipe interna (${emailsInternos.length} e-mails)?`
      : `Disparar este aviso para toda a equipe de vendas E equipe interna?`;

    if (!confirm(confirmMsg)) return;

    setDisparandoAviso(true);
    setErro("");
    setSucesso("");

    try {
      const extras = avisoExtras.split(/[\n,;]+/).map(s => s.trim()).filter(Boolean);
      const res = await dispararAvisoEquipe(
        {
          assunto: avisoAssunto.trim(),
          mensagem: avisoMensagem.trim(),
          publico: avisoPublico,
          prioridade: avisoPrioridade,
          emails_extras: extras
        },
        token
      );
      setSucesso(`✅ ${res.mensagem || "Aviso enviado com sucesso!"}`);
      setAvisoAssunto("");
      setAvisoMensagem("");
      setAvisoExtras("");
    } catch (e) {
      setErro("Erro ao disparar aviso: " + e.message);
    } finally {
      setDisparandoAviso(false);
    }
  }

  // Gerenciamento de e-mails internos
  async function handleAdicionarEmailInterno(e) {
    e.preventDefault();
    const em = novoEmailInterno.trim().toLowerCase();
    if (!em || !em.includes("@")) {
      alert("Digite um e-mail válido.");
      return;
    }
    if (emailsInternos.includes(em)) {
      alert("Este e-mail já está na lista.");
      return;
    }

    const novos = [...emailsInternos, em];
    setEmailsInternos(novos);
    setNovoEmailInterno("");
    setSalvandoInternos(true);
    try {
      await salvarEmailsInternos(novos, token);
      setSucesso(`E-mail ${em} adicionado à equipe interna!`);
      setTimeout(() => setSucesso(""), 3500);
    } catch (e) {
      setErro("Erro ao salvar e-mails internos: " + e.message);
    } finally {
      setSalvandoInternos(false);
    }
  }

  async function handleRemoverEmailInterno(emailParaRemover) {
    if (!confirm(`Remover ${emailParaRemover} da lista de e-mails internos?`)) return;
    const novos = emailsInternos.filter(e => e !== emailParaRemover);
    setEmailsInternos(novos);
    setSalvandoInternos(true);
    try {
      await salvarEmailsInternos(novos, token);
      setSucesso(`E-mail ${emailParaRemover} removido!`);
      setTimeout(() => setSucesso(""), 3500);
    } catch (e) {
      setErro("Erro ao salvar: " + e.message);
    } finally {
      setSalvandoInternos(false);
    }
  }

  // Edição de Contato do Representante (Alterar, Incluir ou Excluir E-mail)
  function handleAbrirEditarRep(r) {
    setRepEmEdicao(r);
    setFormRepEmail(r.email && !r.email.includes("SEM E-MAIL") ? r.email : "");
    setFormRepTelefone(r.telefone || "");
  }

  async function handleSalvarRepEmail(e) {
    if (e) e.preventDefault();
    if (!repEmEdicao) return;

    const emailClean = formRepEmail.trim().toLowerCase();
    if (emailClean && !emailClean.includes("@")) {
      alert("Por favor, informe um endereço de e-mail válido com '@'.");
      return;
    }

    setSalvandoRep(true);
    try {
      const res = await atualizarRepresentanteEmail(
        repEmEdicao.codigo,
        emailClean,
        formRepTelefone,
        token
      );

      const novosReps = representantes.map((r) =>
        r.codigo === repEmEdicao.codigo
          ? { ...r, email: emailClean || null, telefone: formRepTelefone }
          : r
      );
      setRepresentantes(novosReps);

      const comEmail = novosReps.filter(
        (r) => r.ativo && r.email && r.email.includes("@") && !r.email.endsWith(".internal")
      ).length;
      setStats((prev) => ({
        ...prev,
        reps_com_email: comEmail,
        reps_sem_email: novosReps.filter((r) => r.ativo).length - comEmail,
      }));

      setSucesso(res.mensagem || `E-mail do representante #${repEmEdicao.codigo} salvo com sucesso!`);
      setRepEmEdicao(null);
      setTimeout(() => setSucesso(""), 4000);
    } catch (err) {
      alert("Erro ao salvar: " + err.message);
    } finally {
      setSalvandoRep(false);
    }
  }

  async function handleExcluirRepEmail() {
    if (!repEmEdicao) return;
    if (
      !confirm(
        `Deseja realmente remover/excluir o e-mail do representante ${repEmEdicao.nome} (cód. ${repEmEdicao.codigo})? Ele ficará marcado como 'Sem E-mail'.`
      )
    )
      return;

    setSalvandoRep(true);
    try {
      const res = await atualizarRepresentanteEmail(
        repEmEdicao.codigo,
        "",
        formRepTelefone,
        token
      );
      const novosReps = representantes.map((r) =>
        r.codigo === repEmEdicao.codigo
          ? { ...r, email: null, telefone: formRepTelefone }
          : r
      );
      setRepresentantes(novosReps);

      const comEmail = novosReps.filter(
        (r) => r.ativo && r.email && r.email.includes("@") && !r.email.endsWith(".internal")
      ).length;
      setStats((prev) => ({
        ...prev,
        reps_com_email: comEmail,
        reps_sem_email: novosReps.filter((r) => r.ativo).length - comEmail,
      }));

      setSucesso(`E-mail do representante #${repEmEdicao.codigo} removido.`);
      setRepEmEdicao(null);
      setTimeout(() => setSucesso(""), 4000);
    } catch (err) {
      alert("Erro ao remover: " + err.message);
    } finally {
      setSalvandoRep(false);
    }
  }

  const supervisoresUnicos = Array.from(
    new Set(representantes.map(r => r.supervisor).filter(Boolean))
  ).sort();

  const repsModalFiltrados = representantes.filter(r => {
    if (filtroSupervisor !== "todos") {
      if ((r.supervisor || "").toLowerCase() !== filtroSupervisor.toLowerCase()) return false;
    }
    if (buscaModalReps.trim()) {
      const term = buscaModalReps.toLowerCase();
      return (
        (r.codigo || "").toLowerCase().includes(term) ||
        (r.nome || "").toLowerCase().includes(term) ||
        (r.email || "").toLowerCase().includes(term) ||
        (r.supervisor || "").toLowerCase().includes(term)
      );
    }
    return true;
  });

  function toggleRepSelecionado(codigo) {
    const cod = String(codigo);
    setRepsSelecionados(prev =>
      prev.includes(cod) ? prev.filter(c => c !== cod) : [...prev, cod]
    );
  }

  function selecionarTodosFiltrados() {
    const codigosVisiveis = repsModalFiltrados.map(r => String(r.codigo));
    setRepsSelecionados(prev => {
      const set = new Set(prev);
      codigosVisiveis.forEach(c => set.add(c));
      return Array.from(set);
    });
  }

  function limparSelecaoReps() {
    setRepsSelecionados([]);
  }

  const repsFiltrados = representantes.filter(r => {
    if (!buscaRep.trim()) return true;
    const term = buscaRep.toLowerCase();
    return (
      (r.codigo || "").toLowerCase().includes(term) ||
      (r.nome || "").toLowerCase().includes(term) ||
      (r.email || "").toLowerCase().includes(term) ||
      (r.supervisor || "").toLowerCase().includes(term)
    );
  });

  return (
    <div className="admin-modal-backdrop" onClick={onClose}>
      <div className="admin-modal-card rotinas-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="admin-modal-header">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
              <h3>⏰ Configurar Mensagens Automáticas & Rotinas</h3>
              <span className="badge-homologacao-tag">
                🛡️ Modo Teste: envios travados para samuel.mc85@gmail.com
              </span>
            </div>
            <p className="modal-subtitle">
              Gestão de Automações, Alertas Proativos e Avisos para a Equipe de Vendas
            </p>
          </div>
          <button className="admin-modal-close" onClick={onClose}>✕</button>
        </div>

        {/* Abas */}
        <div className="client-settings-tabs">
          <button
            className={`client-tab-btn ${tab === "rotinas" ? "active" : ""}`}
            onClick={() => { setTab("rotinas"); setErro(""); setSucesso(""); }}
          >
            ⏰ Rotinas Automáticas ({rotinas.length})
          </button>
          <button
            className={`client-tab-btn ${tab === "aviso" ? "active" : ""}`}
            onClick={() => { setTab("aviso"); setErro(""); setSucesso(""); }}
          >
            📢 Enviar Aviso Imediato
          </button>
          <button
            className={`client-tab-btn ${tab === "equipe" ? "active" : ""}`}
            onClick={() => { setTab("equipe"); setErro(""); setSucesso(""); }}
          >
            👥 Equipe & E-mails ({stats.total_reps_ativos || 66} reps)
          </button>
        </div>

        {erro && <div className="admin-banner-erro" style={{ margin: "14px 24px 0" }}>⚠️ {erro}</div>}
        {sucesso && <div className="admin-banner-sucesso" style={{ margin: "14px 24px 0" }}>{sucesso}</div>}

        <div className="admin-modal-body" style={{ maxHeight: "72vh", overflowY: "auto", padding: "20px 24px" }}>
          {loading ? (
            <div style={{ padding: "40px", textAlign: "center", color: "#94a3b8" }}>
              Carregando rotinas e mensagens automáticas...
            </div>
          ) : (
            <>
              {/* ── ABA 1: ROTINAS AUTOMÁTICAS ── */}
              {tab === "rotinas" && (
                <div className="rotinas-view-container">
                  {/* Resumo no topo */}
                  <div className="rotinas-stats-banner">
                    <div className="rotinas-stat-box">
                      <span className="stat-label">Rotinas Configuradas</span>
                      <span className="stat-val">{rotinas.length}</span>
                    </div>
                    <div className="rotinas-stat-box">
                      <span className="stat-label">Rotinas Ativas</span>
                      <span className="stat-val highlight" style={{ color: "#34d399" }}>
                        {rotinas.filter(r => r.ativo).length} ativas
                      </span>
                    </div>
                    <div className="rotinas-stat-box">
                      <span className="stat-label">Alcance da Equipe</span>
                      <span className="stat-val">
                        {stats.reps_com_email || 65} representantes + {emailsInternos.length} internos
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={handleAbrirCriar}
                      className="btn-nova-rotina"
                    >
                      ➕ Nova Rotina
                    </button>
                  </div>

                  {/* Barra de Seleção de Representantes para Teste */}
                  <div className="painel-simulacao-rep">
                    <div className="painel-simulacao-header" style={{ marginBottom: repsSelecionados.length > 0 ? "12px" : "0" }}>
                      <div className="painel-simulacao-titulo">
                        <span className="icon-target">🎯</span>
                        <div>
                          <strong>Representantes para Envio / Teste</strong>
                          <p>
                            {repsSelecionados.length === 0
                              ? "Modo Geral Consolidado (1 e-mail com os números da empresa). Clique em Selecionar Representante para escolher 1, vários ou todos."
                              : `${repsSelecionados.length} representante(s) selecionado(s) — será gerado 1 relatório individualizado para cada selecionado em samuel.mc85@gmail.com.`}
                          </p>
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
                        <button
                          type="button"
                          className="btn-abrir-selecao-reps"
                          onClick={() => setModalSelecaoReps(true)}
                        >
                          👥 Selecionar Representante
                          {repsSelecionados.length > 0 && (
                            <span className="badge-count-reps">{repsSelecionados.length}</span>
                          )}
                        </button>
                        {repsSelecionados.length > 0 && (
                          <button
                            type="button"
                            className="btn-limpar-simulacao"
                            onClick={limparSelecaoReps}
                            title="Limpar seleção e voltar para o relatório geral consolidado"
                          >
                            ✕ Limpar
                          </button>
                        )}
                      </div>
                    </div>

                    {repsSelecionados.length > 0 && (
                      <div className="banner-rep-ativo-info">
                        <span className="dot-rep-ativo"></span>
                        <div className="rep-ativo-conteudo" style={{ width: "100%" }}>
                          <div className="rep-ativo-nome" style={{ marginBottom: "6px" }}>
                            Selecionados ({repsSelecionados.length}):
                          </div>
                          <div className="rep-chips-selecionados">
                            {repsSelecionados.slice(0, 8).map(cod => {
                              const rObj = representantes.find(x => String(x.codigo) === String(cod));
                              return (
                                <span key={cod} className="chip-rep-sel">
                                  #{cod} {rObj ? rObj.nome.split(" ")[0] : ""}
                                  <button
                                    type="button"
                                    onClick={() => toggleRepSelecionado(cod)}
                                    title="Remover este representante"
                                  >
                                    ×
                                  </button>
                                </span>
                              );
                            })}
                            {repsSelecionados.length > 8 && (
                              <span className="chip-rep-sel extra">
                                +{repsSelecionados.length - 8} outros
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Lista de Rotinas */}
                  <div className="rotinas-cards-list">
                    {rotinas.map((r) => (
                      <div key={r.id} className={`rotina-card ${r.ativo ? "ativa" : "inativa"}`}>
                        <div className="rotina-card-header">
                          <div className="rotina-title-group">
                            <div className="rotina-header-badges">
                              <span className={`badge-frequencia ${r.frequencia}`}>
                                {r.frequencia === "diario" ? "📅 Diário" : r.frequencia === "semanal" ? "🗓️ Semanal" : "🔄 Periódico"}
                              </span>
                              <span className="badge-canal">
                                {r.canal === "email" ? "✉️ E-mail" : r.canal === "whatsapp" ? "💬 WhatsApp" : "🔔 Portal"}
                              </span>
                              <span className="badge-destinatario">
                                {r.destinatarios_tipo === "equipe_vendas" ? "👥 Equipe de Vendas" : r.destinatarios_tipo === "gestao" ? "👔 Gestão / Diretoria" : "🏢 Todos"}
                              </span>
                              <button
                                type="button"
                                className={`btn-selecionar-rep-card ${repsSelecionados.length > 0 ? "ativo" : ""}`}
                                onClick={() => setModalSelecaoReps(true)}
                                title="Abrir lista para selecionar 1, vários ou todos os representantes"
                              >
                                👥 {repsSelecionados.length === 0
                                  ? "Selecionar Representante"
                                  : repsSelecionados.length === 1
                                  ? `Rep #${repsSelecionados[0]}`
                                  : `${repsSelecionados.length} Reps Selecionados`}
                              </button>
                            </div>
                            <h4 className="rotina-titulo">{r.titulo}</h4>
                          </div>

                          <div className="rotina-toggle-container">
                            <label className="switch-toggle" title={r.ativo ? "Clique para pausar" : "Clique para ativar"}>
                              <input
                                type="checkbox"
                                checked={r.ativo}
                                onChange={() => handleToggleAtivo(r.id)}
                              />
                              <span className="slider round"></span>
                            </label>
                            <span className={`rotina-status-text ${r.ativo ? "ativo" : "inativo"}`}>
                              {r.ativo ? "Ativa" : "Pausada"}
                            </span>
                          </div>
                        </div>

                        <p className="rotina-descricao">{r.descricao}</p>

                        <div className="rotina-detalhes-footer">
                          <div className="rotina-meta-info">
                            <span>⏰ Horário: <strong>{r.horario}</strong></span>
                            {r.dias_semana && r.dias_semana.length > 0 && (
                              <span> • Dias: <strong>{r.dias_semana.join(", ").toUpperCase()}</strong></span>
                            )}
                            {r.ultima_execucao && (
                              <span className="badge-ultimo-disparo" title={`Disparo sob demanda: ${new Date(r.ultima_execucao).toLocaleString('pt-BR')}`}>
                                ⚡ Enviado: {new Date(r.ultima_execucao).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} ({new Date(r.ultima_execucao).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })})
                              </span>
                            )}
                          </div>

                          <div className="rotina-acoes-buttons">
                            <button
                              type="button"
                              className="btn-acao-rotina send-now"
                              onClick={() => handleDispararRotinaAgora(r)}
                              disabled={disparandoRotinaId === r.id}
                              title={
                                repsSelecionados.length > 0
                                  ? `Enviar relatório individualizado para ${repsSelecionados.length} representante(s)`
                                  : "Enviar relatório consolidado geral agora"
                              }
                            >
                              {disparandoRotinaId === r.id
                                ? "⏳ Processando IA..."
                                : repsSelecionados.length === 0
                                ? "🚀 Enviar Agora (Geral)"
                                : repsSelecionados.length === 1
                                ? `🚀 Enviar Rep #${repsSelecionados[0]}`
                                : `🚀 Enviar (${repsSelecionados.length} Reps)`}
                            </button>
                            <button
                              type="button"
                              className="btn-acao-rotina edit"
                              onClick={() => handleAbrirEditar(r)}
                              title="Editar configurações da rotina"
                            >
                              ✏️ Editar
                            </button>
                            <button
                              type="button"
                              className="btn-acao-rotina delete"
                              onClick={() => handleDeletarRotina(r.id)}
                              title="Remover rotina"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── ABA 2: ENVIAR AVISO IMEDIATO ── */}
              {tab === "aviso" && (
                <div className="aviso-view-container">
                  <div className="aviso-info-banner">
                    <div>
                      <strong>📢 Comunicado Oficial / Alerta Rápido</strong>
                      <p>
                        Envie avisos operacionais, mudanças de tabela, incentivos ou alertas de urgência diretamente
                        para a caixa de entrada da equipe de vendas e da equipe interna.
                      </p>
                      <div className="banner-homologacao-box">
                        🛡️ <strong>Trava de Segurança Ativa:</strong> O sistema está em Modo Homologação. Qualquer disparo realizado aqui é direcionado exclusivamente para <strong>samuel.mc85@gmail.com</strong>. Fique tranquilo: nenhum representante receberá e-mails reais.
                      </div>
                    </div>
                  </div>

                  <form onSubmit={handleDispararAviso} className="aviso-form">
                    <div className="form-row-grid">
                      <div className="form-group-custom">
                        <label>Público Destinatário</label>
                        <select
                          value={avisoPublico}
                          onChange={(e) => setAvisoPublico(e.target.value)}
                          className="input-custom-select"
                        >
                          <option value="equipe_vendas">
                            👥 Equipe de Vendas (🔒 Em Teste: envia p/ samuel.mc85@gmail.com)
                          </option>
                          <option value="equipe_interna">
                            🏢 Equipe Interna (🔒 Em Teste: envia p/ samuel.mc85@gmail.com)
                          </option>
                          <option value="todos">
                            🌐 Todos (🔒 Em Teste: envia p/ samuel.mc85@gmail.com)
                          </option>
                        </select>
                      </div>

                      <div className="form-group-custom">
                        <label>Nível de Prioridade</label>
                        <select
                          value={avisoPrioridade}
                          onChange={(e) => setAvisoPrioridade(e.target.value)}
                          className="input-custom-select"
                        >
                          <option value="normal">📢 Normal (Comunicado Oficial)</option>
                          <option value="urgente">🚨 Urgente (Aviso Importante / Bloqueios)</option>
                        </select>
                      </div>
                    </div>

                    <div className="form-group-custom">
                      <label>Assunto do E-mail</label>
                      <input
                        type="text"
                        placeholder="Ex: Campanha de Estoque Pronta Entrega / Atualização Comercial"
                        value={avisoAssunto}
                        onChange={(e) => setAvisoAssunto(e.target.value)}
                        required
                        className="input-custom-text"
                      />
                    </div>

                    <div className="form-group-custom">
                      <label>Mensagem do Comunicado</label>
                      <textarea
                        rows={6}
                        placeholder="Escreva a mensagem que será enviada para toda a equipe..."
                        value={avisoMensagem}
                        onChange={(e) => setAvisoMensagem(e.target.value)}
                        required
                        className="input-custom-textarea"
                      />
                    </div>

                    <div className="form-group-custom">
                      <label>E-mails Extras (Opcional - separados por vírgula ou linha)</label>
                      <input
                        type="text"
                        placeholder="outro@email.com, diretoria@designtextecidos.com.br"
                        value={avisoExtras}
                        onChange={(e) => setAvisoExtras(e.target.value)}
                        className="input-custom-text"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={disparandoAviso}
                      className="btn-disparar-aviso"
                    >
                      {disparandoAviso ? "🚀 Disparando E-mails..." : "🚀 Disparar Aviso para a Equipe Agora"}
                    </button>
                  </form>
                </div>
              )}

              {/* ── ABA 3: EQUIPE & E-MAILS CADASTRADOS ── */}
              {tab === "equipe" && (
                <div className="equipe-view-container">
                  {/* Seção 1: E-mails da Equipe Interna */}
                  <div className="equipe-interna-card">
                    <div className="card-header-flex">
                      <div>
                        <h4>🏢 Equipe Interna (@designtextecidos.com.br)</h4>
                        <p className="card-subtitle-small">
                          Estes e-mails recebem cópia dos alertas de faturamento, pedidos bloqueados e comunicados internos.
                        </p>
                      </div>
                    </div>

                    <form onSubmit={handleAdicionarEmailInterno} className="form-add-interno">
                      <input
                        type="email"
                        placeholder="novo.usuario@designtextecidos.com.br"
                        value={novoEmailInterno}
                        onChange={(e) => setNovoEmailInterno(e.target.value)}
                        className="input-custom-text"
                        style={{ flex: 1 }}
                      />
                      <button type="submit" disabled={salvandoInternos} className="btn-add-interno">
                        ➕ Adicionar
                      </button>
                    </form>

                    <div className="chips-internos-grid">
                      {emailsInternos.map((em) => (
                        <div key={em} className="email-interno-chip">
                          <span>{em}</span>
                          <button
                            type="button"
                            onClick={() => handleRemoverEmailInterno(em)}
                            className="btn-chip-remove"
                            title="Remover e-mail"
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Seção 2: Representantes Comerciais */}
                  <div className="reps-list-card">
                    <div className="reps-header-flex">
                      <div>
                        <h4>👥 Representantes Comerciais ({representantes.filter(r => r.ativo).length} ativos)</h4>
                        <span className="reps-stats-tag">
                          🟢 {stats.reps_com_email || 65} com e-mail cadastrado • 🟡 {stats.reps_sem_email || 1} pendente
                        </span>
                      </div>
                      <input
                        type="text"
                        placeholder="Buscar por código, nome ou e-mail..."
                        value={buscaRep}
                        onChange={(e) => setBuscaRep(e.target.value)}
                        className="input-busca-rep"
                      />
                    </div>

                    <div className="tabela-reps-wrapper">
                      <table className="tabela-reps">
                        <thead>
                          <tr>
                            <th>Cód</th>
                            <th>Representante</th>
                            <th>E-mail Oficial</th>
                            <th>Telefone</th>
                            <th>Supervisor</th>
                            <th>Status E-mail</th>
                            <th style={{ textAlign: "center" }}>Ação</th>
                          </tr>
                        </thead>
                        <tbody>
                          {repsFiltrados.map((r) => {
                            const temEmail = r.email && r.email.includes("@") && !r.email.includes("SEM E-MAIL");
                            return (
                              <tr key={r.codigo}>
                                <td className="col-cod font-mono">{r.codigo}</td>
                                <td className="col-nome font-semibold">{r.nome}</td>
                                <td className="col-email">
                                  {temEmail ? (
                                    <button
                                      type="button"
                                      className="email-link-btn"
                                      onClick={() => handleAbrirEditarRep(r)}
                                      title="Clique para editar este e-mail"
                                    >
                                      {r.email}
                                    </button>
                                  ) : (
                                    <button
                                      type="button"
                                      className="btn-incluir-email"
                                      onClick={() => handleAbrirEditarRep(r)}
                                      title="Clique para cadastrar o e-mail deste representante"
                                    >
                                      ➕ Incluir E-mail
                                    </button>
                                  )}
                                </td>
                                <td className="col-tel text-muted">{r.telefone || "-"}</td>
                                <td className="col-sup">{r.supervisor || "-"}</td>
                                <td>
                                  {temEmail ? (
                                    <span className="badge-status-ok">Pronto para Envio</span>
                                  ) : (
                                    <span className="badge-status-warn">⚠️ Sem E-mail</span>
                                  )}
                                </td>
                                <td style={{ textAlign: "center" }}>
                                  <button
                                    type="button"
                                    className="btn-rep-edit-action"
                                    onClick={() => handleAbrirEditarRep(r)}
                                    title="Editar ou alterar e-mail / contato"
                                  >
                                    ✏️ Editar
                                  </button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* ── MODAL DE CRIAÇÃO / EDIÇÃO DE ROTINA ── */}
        {modalEdicaoRotina && (
          <div className="admin-modal-backdrop sub-modal" onClick={() => setModalEdicaoRotina(false)}>
            <div className="admin-modal-card rotina-edit-card" onClick={(e) => e.stopPropagation()}>
              <div className="admin-modal-header">
                <h3>{rotinaEmEdicao ? "✏️ Editar Rotina Automática" : "➕ Nova Rotina Automática"}</h3>
                <button className="admin-modal-close" onClick={() => setModalEdicaoRotina(false)}>✕</button>
              </div>

              <form onSubmit={handleSalvarRotina} className="form-rotina-edit">
                <div className="form-group-custom">
                  <label>Título da Rotina</label>
                  <input
                    type="text"
                    value={formRotina.titulo}
                    onChange={(e) => setFormRotina({ ...formRotina, titulo: e.target.value })}
                    placeholder="Ex: Alerta de Pedidos Retidos no Financeiro"
                    required
                    className="input-custom-text"
                  />
                </div>

                <div className="form-group-custom">
                  <label>Descrição do Objetivo</label>
                  <input
                    type="text"
                    value={formRotina.descricao}
                    onChange={(e) => setFormRotina({ ...formRotina, descricao: e.target.value })}
                    placeholder="Ex: Notifica representantes com pedidos que precisam de liberação de alçada."
                    className="input-custom-text"
                  />
                </div>

                <div className="form-row-grid">
                  <div className="form-group-custom">
                    <label>Frequência</label>
                    <select
                      value={formRotina.frequencia}
                      onChange={(e) => setFormRotina({ ...formRotina, frequencia: e.target.value })}
                      className="input-custom-select"
                    >
                      <option value="diario">Diário</option>
                      <option value="semanal">Semanal</option>
                      <option value="quinzenal">Quinzenal</option>
                      <option value="mensal">Mensal</option>
                    </select>
                  </div>

                  <div className="form-group-custom">
                    <label>Horário do Disparo</label>
                    <input
                      type="time"
                      value={formRotina.horario}
                      onChange={(e) => setFormRotina({ ...formRotina, horario: e.target.value })}
                      className="input-custom-text"
                    />
                  </div>
                </div>

                <div className="form-row-grid">
                  <div className="form-group-custom">
                    <label>Canal de Envio</label>
                    <select
                      value={formRotina.canal}
                      onChange={(e) => setFormRotina({ ...formRotina, canal: e.target.value })}
                      className="input-custom-select"
                    >
                      <option value="email">✉️ E-mail</option>
                      <option value="whatsapp">💬 WhatsApp (Via Deise IA)</option>
                      <option value="portal">🔔 Notificação no Portal</option>
                    </select>
                  </div>

                  <div className="form-group-custom">
                    <label>Público Alvo</label>
                    <select
                      value={formRotina.destinatarios_tipo}
                      onChange={(e) => setFormRotina({ ...formRotina, destinatarios_tipo: e.target.value })}
                      className="input-custom-select"
                    >
                      <option value="equipe_vendas">👥 Equipe de Vendas (🔒 Em Testes: envia p/ samuel.mc85@gmail.com)</option>
                      <option value="gestao">👔 Apenas Gestão / Supervisores (🔒 Em Testes: envia p/ samuel.mc85@gmail.com)</option>
                      <option value="equipe_interna">🏢 Equipe Interna (🔒 Em Testes: envia p/ samuel.mc85@gmail.com)</option>
                      <option value="todos">🌐 Todos (🔒 Em Testes: envia p/ samuel.mc85@gmail.com)</option>
                    </select>
                  </div>
                </div>

                <div className="banner-homologacao-box" style={{ margin: "0 0 16px 0" }}>
                  🛡️ <strong>Trava de Segurança (Modo Homologação Ativo):</strong> As rotinas configuradas são regras salvas no sistema e <u>não realizam disparos automáticos para representantes</u> sem a sua autorização expressa. Qualquer teste disparado é redirecionado exclusivamente para <strong>samuel.mc85@gmail.com</strong>.
                </div>

                <div className="form-group-custom">
                  <label>Template da Mensagem / Orientação</label>
                  <textarea
                    rows={4}
                    value={formRotina.mensagem_template}
                    onChange={(e) => setFormRotina({ ...formRotina, mensagem_template: e.target.value })}
                    placeholder="Instruções ou corpo padrão da mensagem..."
                    className="input-custom-textarea"
                  />
                </div>

                <div className="modal-actions-bar">
                  <button type="button" onClick={() => setModalEdicaoRotina(false)} className="btn-cancelar">
                    Cancelar
                  </button>
                  <button type="submit" className="btn-salvar-modal">
                    Salvar Rotina
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ── SUB-MODAL: EDITAR / INCLUIR / EXCLUIR E-MAIL DE REPRESENTANTE ── */}
        {repEmEdicao && (
          <div className="admin-modal-backdrop sub-modal" onClick={() => !salvandoRep && setRepEmEdicao(null)}>
            <div className="admin-modal-card rep-edit-card" onClick={(e) => e.stopPropagation()}>
              <div className="admin-modal-header">
                <div>
                  <h3>✏️ Editar Contato do Representante</h3>
                  <div className="rep-subheading-cod">
                    Representante <strong>#{repEmEdicao.codigo}</strong>
                  </div>
                </div>
                <button
                  className="admin-modal-close"
                  onClick={() => !salvandoRep && setRepEmEdicao(null)}
                  disabled={salvandoRep}
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleSalvarRepEmail} className="form-rep-edit-body">
                <div className="rep-detail-box">
                  <div className="rep-detail-item">
                    <span className="rep-detail-label">Nome:</span>
                    <strong className="rep-detail-val">{repEmEdicao.nome}</strong>
                  </div>
                  <div className="rep-detail-item">
                    <span className="rep-detail-label">Supervisor:</span>
                    <span className="rep-detail-val">{repEmEdicao.supervisor || "Não atribuído"}</span>
                  </div>
                </div>

                <div className="form-group-custom">
                  <label>E-mail Oficial (para Avisos & Mensagens Automáticas)</label>
                  <input
                    type="email"
                    value={formRepEmail}
                    onChange={(e) => setFormRepEmail(e.target.value)}
                    placeholder="exemplo@representante.com.br"
                    className="input-custom-text input-destaque-email"
                    autoFocus
                  />
                  <small className="field-hint">
                    Deixe em branco ou use o botão "Excluir E-mail" para remover o e-mail do representante.
                  </small>
                </div>

                <div className="form-group-custom">
                  <label>Telefone / WhatsApp</label>
                  <input
                    type="text"
                    value={formRepTelefone}
                    onChange={(e) => setFormRepTelefone(e.target.value)}
                    placeholder="(00) 00000-0000"
                    className="input-custom-text"
                  />
                </div>

                <div className="modal-actions-bar rep-modal-actions-bar">
                  <div>
                    {repEmEdicao.email && !repEmEdicao.email.includes("SEM E-MAIL") && (
                      <button
                        type="button"
                        onClick={handleExcluirRepEmail}
                        disabled={salvandoRep}
                        className="btn-excluir-rep-email"
                        title="Remover e-mail cadastrado"
                      >
                        🗑️ Excluir E-mail
                      </button>
                    )}
                  </div>
                  <div className="rep-modal-btns-right">
                    <button
                      type="button"
                      onClick={() => setRepEmEdicao(null)}
                      disabled={salvandoRep}
                      className="btn-cancelar"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={salvandoRep}
                      className="btn-salvar-modal"
                    >
                      {salvandoRep ? "Salvando..." : "💾 Salvar Alterações"}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ── SUB-MODAL: SELECIONAR 1, VÁRIOS OU TODOS OS REPRESENTANTES ── */}
        {modalSelecaoReps && (
          <div className="admin-modal-backdrop sub-modal" onClick={() => setModalSelecaoReps(false)}>
            <div className="admin-modal-card selecao-reps-modal-card" onClick={(e) => e.stopPropagation()}>
              <div className="admin-modal-header">
                <div>
                  <h3>👥 Selecionar Representante(s)</h3>
                  <p className="modal-subtitle">
                    Marque 1, vários ou todos os representantes para testar os relatórios individualizados em <strong>samuel.mc85@gmail.com</strong>
                  </p>
                </div>
                <button className="admin-modal-close" onClick={() => setModalSelecaoReps(false)}>✕</button>
              </div>

              <div className="selecao-reps-toolbar">
                <input
                  type="text"
                  className="input-custom-text"
                  placeholder="🔍 Digite o código, nome, representação ou e-mail..."
                  value={buscaModalReps}
                  onChange={(e) => setBuscaModalReps(e.target.value)}
                  autoFocus
                  style={{ flex: 1, minWidth: "220px" }}
                />
                <select
                  className="select-simulacao"
                  value={filtroSupervisor}
                  onChange={(e) => setFiltroSupervisor(e.target.value)}
                >
                  <option value="todos">🌐 Todos os Supervisores</option>
                  {supervisoresUnicos.map((sup) => (
                    <option key={sup} value={sup}>👔 Sup: {sup}</option>
                  ))}
                </select>
              </div>

              <div className="selecao-reps-actions-row">
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  <button
                    type="button"
                    className="btn-selecao-rapida all"
                    onClick={selecionarTodosFiltrados}
                  >
                    ☑️ Selecionar Todos ({repsModalFiltrados.length})
                  </button>
                  <button
                    type="button"
                    className="btn-selecao-rapida clear"
                    onClick={limparSelecaoReps}
                  >
                    🔲 Desmarcar Todos (Visão Geral)
                  </button>
                </div>
                <span className="selecao-reps-counter">
                  {repsSelecionados.length === 0
                    ? "Visão Geral (0 selecionados)"
                    : `${repsSelecionados.length} selecionado(s)`}
                </span>
              </div>

              <div className="selecao-reps-list">
                {repsModalFiltrados.map((rep) => {
                  const cod = String(rep.codigo);
                  const checked = repsSelecionados.includes(cod);
                  return (
                    <label key={cod} className={`selecao-rep-item ${checked ? "checked" : ""}`}>
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleRepSelecionado(cod)}
                      />
                      <div className="selecao-rep-info">
                        <div className="selecao-rep-top">
                          <span className="selecao-rep-cod">#{cod}</span>
                          <span className="selecao-rep-nome">{rep.nome}</span>
                          {rep.supervisor && (
                            <span className="selecao-rep-sup">👔 {rep.supervisor}</span>
                          )}
                        </div>
                        <div className="selecao-rep-sub">
                          <span>✉️ {rep.email || "Sem e-mail cadastrado"}</span>
                          {rep.meta ? (
                            <span> • 🎯 Meta: {Number(rep.meta).toLocaleString("pt-BR")} m</span>
                          ) : null}
                        </div>
                      </div>
                    </label>
                  );
                })}
                {repsModalFiltrados.length === 0 && (
                  <div style={{ padding: "30px", textAlign: "center", color: "#94a3b8" }}>
                    Nenhum representante encontrado com esse filtro.
                  </div>
                )}
              </div>

              <div className="modal-actions-bar" style={{ padding: "14px 24px", borderTop: "1px solid rgba(255,255,255,0.08)", marginTop: 0 }}>
                <button
                  type="button"
                  className="btn-cancelar"
                  onClick={limparSelecaoReps}
                >
                  Limpar (Geral)
                </button>
                <button
                  type="button"
                  className="btn-salvar-modal"
                  onClick={() => setModalSelecaoReps(false)}
                >
                  ✅ Confirmar ({repsSelecionados.length === 0 ? "Geral" : `${repsSelecionados.length} selecionado(s)`})
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
