import { useState } from "react";
import { updateAdminTenant } from "../api";

export default function ContractModal({ tenant, token, onSalvarContrato, onClose }) {
  const [editando, setEditando] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");

  const contratoAtual = tenant.contrato || {};
  const [formContrato, setFormContrato] = useState({
    numero_contrato: contratoAtual.numero_contrato || `DSM-CNX-2026/${tenant.id?.slice(0, 4).toUpperCase()}`,
    contratada_razao: contratoAtual.contratada_razao || "DSM Empreendimentos Digitais Ltda",
    contratada_cnpj: contratoAtual.contratada_cnpj || "00.000.000/0001-00",
    produto: contratoAtual.produto || "CONEXO.dev - Inteligência Comercial com IA",
    data_inicio: contratoAtual.data_inicio || (tenant.created_at ? tenant.created_at.split("T")[0] : "2026-08-01"),
    vigencia_meses: contratoAtual.vigencia_meses || 12,
    renovacao_automatica: contratoAtual.renovacao_automatica !== false,
    valor_mensal: contratoAtual.valor_mensal || tenant.valor_mensal || 3500.0,
    dia_vencimento: contratoAtual.dia_vencimento || tenant.dia_vencimento || 10,
    sla_garantido: contratoAtual.sla_garantido || "99.5%",
    suporte_nivel: contratoAtual.suporte_nivel || "Prioritário WhatsApp + Chamados",
    observacoes: contratoAtual.observacoes || "Integração multissistemas via APIs com ERPs da contratante.",
  });

  async function handleSalvar(e) {
    e.preventDefault();
    setSalvando(true);
    setErro("");
    setSucesso("");
    try {
      await updateAdminTenant(tenant.id, { contrato: formContrato }, token);
      setSucesso("Termos do contrato salvos com sucesso!");
      onSalvarContrato(tenant.id, formContrato);
      setTimeout(() => {
        setSucesso("");
        setEditando(false);
      }, 1500);
    } catch (err) {
      setErro("Erro ao salvar contrato: " + err.message);
    } finally {
      setSalvando(false);
    }
  }

  function handleImprimir() {
    window.print();
  }

  return (
    <div className="admin-modal-backdrop" onClick={onClose}>
      <div className="admin-modal-card" style={{ maxWidth: "860px", width: "95%" }} onClick={(e) => e.stopPropagation()}>
        <div className="admin-modal-header">
          <div>
            <h3>📜 Contrato de Prestação de Serviços de Software (SaaS)</h3>
            <p className="modal-subtitle">
              DSM Empreendimentos Digitais Ltda × <strong>{tenant.nome_fantasia || tenant.nome}</strong>
            </p>
          </div>
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <button
              className="btn-admin-action"
              onClick={() => setEditando(!editando)}
              style={{ background: editando ? "#38bdf8" : "rgba(255,255,255,0.08)", color: editando ? "#0f172a" : "#f8fafc", padding: "6px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.15)", cursor: "pointer", fontSize: "12px", fontWeight: "600" }}
            >
              {editando ? "👁️ Modo Leitura" : "✏️ Editar Termos"}
            </button>
            <button
              className="btn-admin-action"
              onClick={handleImprimir}
              style={{ background: "#22c55e", color: "#052e16", padding: "6px 14px", borderRadius: "8px", border: "none", cursor: "pointer", fontSize: "12px", fontWeight: "700" }}
            >
              🖨️ Imprimir / PDF
            </button>
            <button className="admin-modal-close" onClick={onClose}>✕</button>
          </div>
        </div>

        {erro && <div className="admin-banner-erro" style={{ margin: "12px 24px 0" }}>⚠️ {erro}</div>}
        {sucesso && <div className="admin-banner-sucesso" style={{ margin: "12px 24px 0" }}>✅ {sucesso}</div>}

        <div className="admin-modal-body" style={{ maxHeight: "74vh", overflowY: "auto", padding: "20px" }}>
          {editando ? (
            <form onSubmit={handleSalvar} className="client-settings-form">
              <div className="grid-2-cols">
                <div className="form-group-admin">
                  <label>Número do Contrato</label>
                  <input
                    type="text"
                    value={formContrato.numero_contrato}
                    onChange={(e) => setFormContrato({ ...formContrato, numero_contrato: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group-admin">
                  <label>Data de Início da Vigência</label>
                  <input
                    type="date"
                    value={formContrato.data_inicio}
                    onChange={(e) => setFormContrato({ ...formContrato, data_inicio: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid-2-cols">
                <div className="form-group-admin">
                  <label>Vigência (Meses)</label>
                  <input
                    type="number"
                    value={formContrato.vigencia_meses}
                    onChange={(e) => setFormContrato({ ...formContrato, vigencia_meses: Number(e.target.value) })}
                    required
                  />
                </div>
                <div className="form-group-admin">
                  <label>Renovação Automática</label>
                  <select
                    value={formContrato.renovacao_automatica ? "true" : "false"}
                    onChange={(e) => setFormContrato({ ...formContrato, renovacao_automatica: e.target.value === "true" })}
                  >
                    <option value="true">Sim (Renovação Automática por igual período)</option>
                    <option value="false">Não (Encerramento no termo)</option>
                  </select>
                </div>
              </div>

              <div className="grid-2-cols">
                <div className="form-group-admin">
                  <label>Valor Mensal da Assinatura (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formContrato.valor_mensal}
                    onChange={(e) => setFormContrato({ ...formContrato, valor_mensal: Number(e.target.value) })}
                    required
                  />
                </div>
                <div className="form-group-admin">
                  <label>Dia de Vencimento Mensal</label>
                  <input
                    type="number"
                    min="1"
                    max="31"
                    value={formContrato.dia_vencimento}
                    onChange={(e) => setFormContrato({ ...formContrato, dia_vencimento: Number(e.target.value) })}
                    required
                  />
                </div>
              </div>

              <div className="grid-2-cols">
                <div className="form-group-admin">
                  <label>SLA Garantido de Disponibilidade</label>
                  <input
                    type="text"
                    value={formContrato.sla_garantido}
                    onChange={(e) => setFormContrato({ ...formContrato, sla_garantido: e.target.value })}
                    placeholder="99.5%"
                  />
                </div>
                <div className="form-group-admin">
                  <label>Nível de Suporte</label>
                  <input
                    type="text"
                    value={formContrato.suporte_nivel}
                    onChange={(e) => setFormContrato({ ...formContrato, suporte_nivel: e.target.value })}
                    placeholder="Prioritário WhatsApp + Chamados"
                  />
                </div>
              </div>

              <div className="form-group-admin">
                <label>Observações / Cláusulas Específicas</label>
                <textarea
                  rows={3}
                  value={formContrato.observacoes}
                  onChange={(e) => setFormContrato({ ...formContrato, observacoes: e.target.value })}
                  placeholder="Detalhes específicos sobre as integrações, APIs de ERPs conectados ou condições comerciais..."
                />
              </div>

              <div className="modal-actions-right" style={{ marginTop: "16px" }}>
                <button type="submit" className="btn-primary-admin" disabled={salvando}>
                  {salvando ? "Salvando Contrato..." : "💾 Salvar Termos do Contrato"}
                </button>
              </div>
            </form>
          ) : (
            /* Minuta Formatada em Formato Documento Jurídico */
            <div className="minuta-contrato-doc">
              <div className="minuta-header">
                <h2>INSTRUMENTO PARTICULAR DE CONTRATO DE PRESTAÇÃO DE SERVIÇOS E LICENCIAMENTO DE SOFTWARE (SaaS)</h2>
                <p>Nº DE REGISTRO: <strong>{formContrato.numero_contrato}</strong> · PRODUTO: <strong>CONEXO.dev</strong></p>
              </div>

              <div className="minuta-clausula">
                <h4>DAS PARTES CONTRATANTES</h4>
                <p>
                  <strong>CONTRATADA:</strong> <strong>{formContrato.contratada_razao}</strong>, pessoa jurídica de direito privado, desenvolvedora e proprietária da plataforma de inteligência artificial comercial <strong>CONEXO.dev</strong>.
                </p>
                <p style={{ marginTop: "8px" }}>
                  <strong>CONTRATANTE:</strong> <strong>{tenant.nome}</strong> (Nome Fantasia: <em>{tenant.nome_fantasia || tenant.nome}</em>), inscrita no CNPJ sob o nº <strong>{tenant.cnpj}</strong>.
                </p>
              </div>

              <div className="minuta-clausula">
                <h4>CLÁUSULA 1ª – DO OBJETO</h4>
                <p>
                  O presente contrato tem como objeto o fornecimento, disponibilização de acesso e licenciamento de uso contínuo da plataforma <strong>CONEXO.dev</strong>, solução SaaS de Inteligência Artificial para Gestão Comercial, Análise Preditiva e Unificação de Pedidos/Estoque conectada diretamente aos sistemas de gestão (ERPs, APIs e bancos de dados) da <strong>CONTRATANTE</strong>.
                </p>
              </div>

              <div className="minuta-clausula">
                <h4>CLÁUSULA 2ª – DOS NÍVEIS DE SERVIÇO E SUPORTE (SLA)</h4>
                <p>
                  A <strong>CONTRATADA</strong> compromete-se a manter uma taxa de disponibilidade média de <strong>{formContrato.sla_garantido}</strong>, prestando suporte técnico em nível <strong>{formContrato.suporte_nivel}</strong>, com resposta ágil a chamados e monitoramento contínuo das rotinas de integração de dados.
                </p>
              </div>

              <div className="minuta-clausula">
                <h4>CLÁUSULA 3ª – DA CONFIDENCIALIDADE, PROTEÇÃO DE DADOS (LGPD) E SEGURANÇA</h4>
                <p>
                  Todas as informações comerciais, métricas financeiras, carteira de clientes, pedidos e estoques aos quais a <strong>CONTRATADA</strong> tiver acesso são de propriedade exclusiva da <strong>CONTRATANTE</strong>, obrigando-se as partes a manter sigilo rigoroso e aplicar padrões de criptografia e conformidade estrita com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018).
                </p>
              </div>

              <div className="minuta-clausula">
                <h4>CLÁUSULA 4ª – DO VALOR, FATURAMENTO E VENCIMENTO</h4>
                <p>
                  Pelos serviços ora contratados, a <strong>CONTRATANTE</strong> pagará à <strong>CONTRATADA</strong> o valor mensal de <strong>R$ {Number(formContrato.valor_mensal).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}</strong>, com vencimento programado para todo <strong>dia {formContrato.dia_vencimento}</strong> de cada mês subsequente ao período de utilização.
                </p>
              </div>

              <div className="minuta-clausula">
                <h4>CLÁUSULA 5ª – DA VIGÊNCIA E RENOVAÇÃO</h4>
                <p>
                  O presente instrumento entra em vigor em <strong>{formContrato.data_inicio ? new Date(formContrato.data_inicio).toLocaleDateString("pt-BR") : "01/08/2026"}</strong>, com vigência estipulada em <strong>{formContrato.vigencia_meses} meses</strong>, {formContrato.renovacao_automatica ? "renovando-se automaticamente por períodos iguais e sucessivos caso não haja manifestação expressa em contrário com antecedência de 30 (trinta) dias." : "encerrando-se de pleno direito ao fim do prazo pactuado."}
                </p>
              </div>

              {formContrato.observacoes && (
                <div className="minuta-clausula">
                  <h4>CLÁUSULA 6ª – DAS DISPOSIÇÕES ESPECÍFICAS DA INTEGRAÇÃO</h4>
                  <p>{formContrato.observacoes}</p>
                </div>
              )}

              <div className="minuta-assinaturas">
                <div>
                  <div className="linha-assinatura">
                    <strong>{formContrato.contratada_razao}</strong><br />
                    <span>CONTRATADA — CONEXO.dev</span>
                  </div>
                </div>
                <div>
                  <div className="linha-assinatura">
                    <strong>{tenant.nome}</strong><br />
                    <span>CONTRATANTE — Representante Legal</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
