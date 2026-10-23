const BASE = import.meta.env.VITE_API_URL;

// ── Pergunta (resposta JSON completa) ───────────────────────
export async function perguntar(pergunta, historico, token) {
  const r = await fetch(`${BASE}/conexo/perguntar`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ pergunta, historico }),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro na consulta");
  return r.json(); // { tipo, conteudo, intent, dados }
}

// ── Pergunta com streaming (SSE) ────────────────────────────
export async function perguntarStream(
  pergunta,
  historico,
  token,
  onDados,
  onDelta,
  onFim
) {
  const r = await fetch(`${BASE}/conexo/perguntar-stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ pergunta, historico }),
  });

  if (!r.ok) throw new Error("Erro na conexão com NEXO");

  const reader = r.body.getReader();
  const dec = new TextDecoder();
  let buf = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const linhas = buf.split("\n\n");
    buf = linhas.pop();
    for (const l of linhas) {
      if (!l.startsWith("data: ")) continue;
      try {
        const ev = JSON.parse(l.slice(6));
        if (ev.tipo === "dados") onDados(ev.intent, ev.dados);
        else if (ev.tipo === "texto") onDelta(ev.delta);
        else if (ev.tipo === "fim") onFim();
      } catch {
        // linha malformada, ignora
      }
    }
  }
}

// ── Transcrição de áudio (Whisper) com retry automático ──────
export async function transcrever(blob, token) {
  const type = blob.type || "";
  let ext = "webm";
  if (type.includes("mp4") || type.includes("aac") || type.includes("m4a")) {
    ext = "m4a";
  } else if (type.includes("wav")) {
    ext = "wav";
  } else if (type.includes("ogg")) {
    ext = "ogg";
  }
  
  const fd = new FormData();
  fd.append("audio", blob, `fala.${ext}`);

  let tentativas = 0;
  const maxTentativas = 2;

  while (tentativas < maxTentativas) {
    try {
      const r = await fetch(`${BASE}/conexo/transcrever`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      });

      if (!r.ok) {
        const errData = await r.json().catch(() => ({}));
        throw new Error(errData.detail || "Falha ao processar o áudio");
      }

      const data = await r.json();
      return data.texto;
    } catch (err) {
      tentativas++;
      if (tentativas >= maxTentativas) {
        if (err.name === "TypeError" || err.message.includes("fetch")) {
          throw new Error("Conexão instável com o servidor. Aguarde alguns segundos e tente gravar novamente.");
        }
        throw err;
      }
      // Aguarda 1 segundo antes de tentar novamente (caso o servidor esteja acordando)
      await new Promise((res) => setTimeout(res, 1000));
    }
  }
}

// ── Alertas ─────────────────────────────────────────────────
export async function falar(texto, token) {
  const r = await fetch(`${BASE}/conexo/falar`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ texto }),
  });
  if (!r.ok) throw new Error("Falha ao gerar voz");
  return r.blob();
}

export async function buscarAlertas(token) {
  const r = await fetch(`${BASE}/conexo/alertas`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) return [];
  return (await r.json()).alertas || [];
}

export async function marcarAlertaLido(id, token) {
  await fetch(`${BASE}/conexo/alertas/${id}/lido`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
  });
}

// ── Cadastro ─────────────────────────────────────────────────
export async function cadastrar(cnpj, email, senha, setor) {
  const r = await fetch(`${BASE}/conexo/cadastro`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cnpj, email, senha, setor }),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro no cadastro");
  return r.json();
}

// ── Funções Administrativas Master (/admin) ───────────────────
function getAdminHeaders(token, adminKey) {
  const headers = { "Content-Type": "application/json" };
  if (adminKey) {
    headers["X-Admin-Key"] = adminKey;
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export async function getAdminOverview(token, adminKey) {
  const r = await fetch(`${BASE}/conexo/admin/overview`, {
    headers: getAdminHeaders(token, adminKey),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao carregar dados do painel admin");
  return r.json();
}

export async function getAdminTenants(token, adminKey) {
  const r = await fetch(`${BASE}/conexo/admin/tenants`, {
    headers: getAdminHeaders(token, adminKey),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao listar empresas");
  return r.json();
}

export async function createAdminTenant(dados, token, adminKey) {
  const r = await fetch(`${BASE}/conexo/admin/tenants`, {
    method: "POST",
    headers: getAdminHeaders(token, adminKey),
    body: JSON.stringify(dados),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao criar empresa");
  return r.json();
}

export async function updateAdminTenant(tenantId, dados, token, adminKey) {
  const r = await fetch(`${BASE}/conexo/admin/tenants/${tenantId}`, {
    method: "PUT",
    headers: getAdminHeaders(token, adminKey),
    body: JSON.stringify(dados),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao atualizar empresa");
  return r.json();
}

export async function getAdminConnectors(tenantId, token, adminKey) {
  const r = await fetch(`${BASE}/conexo/admin/tenants/${tenantId}/connectors`, {
    headers: getAdminHeaders(token, adminKey),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao carregar conectores");
  return r.json();
}

export async function saveAdminConnectors(tenantId, conectores, token, adminKey) {
  const r = await fetch(`${BASE}/conexo/admin/tenants/${tenantId}/connectors`, {
    method: "POST",
    headers: getAdminHeaders(token, adminKey),
    body: JSON.stringify({ conectores }),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao salvar conectores");
  return r.json();
}

export async function testAdminConnector(tipo, config, token, adminKey) {
  const r = await fetch(`${BASE}/conexo/admin/connectors/test`, {
    method: "POST",
    headers: getAdminHeaders(token, adminKey),
    body: JSON.stringify({ tipo, config }),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao testar conector");
  return r.json();
}

export async function getAdminUsers(tenantId, token, adminKey) {
  const url = tenantId ? `${BASE}/conexo/admin/users?tenant_id=${tenantId}` : `${BASE}/conexo/admin/users`;
  const r = await fetch(url, {
    headers: getAdminHeaders(token, adminKey),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao listar usuários");
  return r.json();
}

export async function createAdminUser(dados, token, adminKey) {
  const r = await fetch(`${BASE}/conexo/admin/users`, {
    method: "POST",
    headers: getAdminHeaders(token, adminKey),
    body: JSON.stringify(dados),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao criar usuário");
  return r.json();
}

export async function resetAdminUserPassword(userId, novaSenha, token, adminKey) {
  const r = await fetch(`${BASE}/conexo/admin/users/${userId}/reset-password`, {
    method: "POST",
    headers: getAdminHeaders(token, adminKey),
    body: JSON.stringify({ nova_senha: novaSenha }),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao redefinir senha");
  return r.json();
}

export async function updateAdminUser(userId, dados, token, adminKey) {
  const r = await fetch(`${BASE}/conexo/admin/users/${userId}`, {
    method: "PUT",
    headers: getAdminHeaders(token, adminKey),
    body: JSON.stringify(dados),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao atualizar usuário");
  return r.json();
}

export async function deleteAdminUser(userId, token, adminKey) {
  const r = await fetch(`${BASE}/conexo/admin/users/${userId}`, {
    method: "DELETE",
    headers: getAdminHeaders(token, adminKey),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao excluir usuário");
  return r.json();
}

export async function getAdminLogs(params, token, adminKey) {
  const qs = new URLSearchParams(params || {}).toString();
  const r = await fetch(`${BASE}/conexo/admin/logs?${qs}`, {
    headers: getAdminHeaders(token, adminKey),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao carregar logs");
  return r.json();
}

export async function getAdminFinanceiro(token, adminKey) {
  const r = await fetch(`${BASE}/conexo/admin/financeiro`, {
    headers: getAdminHeaders(token, adminKey),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Erro ao carregar dados financeiros SaaS");
  return r.json();
}
