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

// ── Transcrição de áudio (Whisper) ──────────────────────────
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
  const r = await fetch(`${BASE}/conexo/transcrever`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
  });
  if (!r.ok) throw new Error("Falha ao transcrever áudio");
  return (await r.json()).texto;
}

// ── Alertas ─────────────────────────────────────────────────
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
