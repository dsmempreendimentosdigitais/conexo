# NEXO v2.0 — Guia Completo

## Estrutura completa do projeto

```
nexo/
├── main.py                      # FastAPI v2.0 — todos os endpoints
├── config.py                    # Variáveis de ambiente
├── tools.py                     # 11 tools (10 RPCs + inteligência de mercado)
├── prompts.py                   # System prompts com memória de conversa
├── router.py                    # Roteador com histórico (gpt-4o-mini)
├── executor.py                  # Executor multi-tenant + mercado
├── formatter.py                 # Formatter com suporte a mercado
├── logger.py                    # Auditoria em nexo_logs
├── auth.py                      # Extrai tenant/perfil do token JWT
├── requirements.txt
│
├── onboarding/                  # Onboarding técnico por IA
│   ├── __init__.py
│   ├── analista.py              # Analisa schema → mapeamento semântico
│   ├── gerador.py               # Mapeamento → 10 RPCs SQL
│   └── rotas.py                 # Endpoints admin /nexo/onboarding/*
│
├── mercado/                     # Inteligência de mercado (Fase 2)
│   ├── __init__.py
│   ├── busca.py                 # Busca web via Tavily
│   └── motor.py                 # Cruzamento dados internos × mercado
│
├── jobs/                        # Jobs agendados (cron)
│   ├── __init__.py
│   ├── alertas.py               # Alertas internos (queda fat., inativos)
│   └── alertas_mercado.py       # Alertas de mercado (insumos)
│
├── supabase_setup.sql           # SQL completo v2.0
├── Dockerfile
├── docker-compose.yml
├── nginx.conf                   # Proxy reverso nexo.dsmsys.com.br
├── .env.example
└── nexo-pwa/                    # Frontend React PWA
    ├── package.json
    ├── vite.config.js
    ├── index.html
    ├── .env.example
    └── src/
        ├── main.jsx
        ├── App.jsx              # Login + Cadastro + Chat
        ├── api.js               # Chamadas ao backend
        ├── auth.js              # Supabase auth
        ├── styles.css           # Design system dark
        └── components/
            ├── Chat.jsx         # Interface principal (texto + áudio + stream)
            ├── Message.jsx      # Bolha de mensagem
            ├── Dashboard.jsx    # Gráficos automáticos por intent
            └── AlertPanel.jsx   # Painel de alertas proativos
```

---

## Funcionalidades implementadas (v2.0)

| Camada | Funcionalidade | Status |
|---|---|---|
| Segurança | Auth JWT + isolamento multi-tenant (3 camadas) | ✅ |
| Banco | 10 RPCs com `p_tenant` + RLS | ✅ |
| Backend | Roteador com memória de conversa | ✅ |
| Backend | Streaming SSE (tempo real) | ✅ |
| Backend | Transcrição de áudio (Whisper) | ✅ |
| Backend | Alertas internos proativos | ✅ |
| Backend | Onboarding técnico por IA | ✅ |
| Fase 2 | Inteligência de mercado (Tavily + LLM) | ✅ |
| Fase 2 | Cruzamento dado interno × mercado | ✅ |
| Fase 2 | Alertas de mercado proativos | ✅ |
| Frontend | PWA instalável (Android/iOS/desktop) | ✅ |
| Frontend | Login / Cadastro por CNPJ | ✅ |
| Frontend | Chat com streaming em tempo real | ✅ |
| Frontend | Gravação de áudio no celular | ✅ |
| Frontend | Dashboards automáticos por intent | ✅ |
| Frontend | Sino de alertas com contagem | ✅ |
| Deploy | Docker + Nginx para nexo.dsmsys.com.br | ✅ |

---

## Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| POST | `/nexo/perguntar` | Pergunta — resposta JSON completa |
| POST | `/nexo/perguntar-stream` | Pergunta — streaming SSE em tempo real |
| POST | `/nexo/transcrever` | Áudio → texto (Whisper) |
| GET  | `/nexo/alertas` | Lista alertas não lidos do tenant |
| PATCH | `/nexo/alertas/{id}/lido` | Marca alerta como lido |
| POST | `/nexo/cadastro` | Cria usuário (vincula ao tenant pelo CNPJ) |
| POST | `/nexo/onboarding/analisar` | Admin: analisa schema de novo cliente |
| POST | `/nexo/onboarding/gerar` | Admin: gera as 10 RPCs SQL |
| GET  | `/health` | Health check |

---

## Variáveis de ambiente necessárias

### Backend (`.env`)
```env
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...     # service_role — nunca no front
NEXO_ADMIN_KEY=chave-forte-32chars
TAVILY_API_KEY=tvly-...         # opcional — desabilita mercado se vazio
```

### Frontend (`nexo-pwa/.env`)
```env
VITE_API_URL=https://nexo.dsmsys.com.br
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...   # anon — pode ir ao front (RLS protege)
```

---

## Deploy passo a passo

### 1. Supabase — rodar o SQL
```
SQL Editor → colar supabase_setup.sql → executar
Adaptar nomes de tabelas (⚠️ AJUSTAR) para o schema real do seu banco
Auth → habilitar Email/Password
Confirmar que RLS está ativo em todas as tabelas de dados
```

### 2. Backend — Docker + Nginx
```bash
# Copiar e preencher .env
cp .env.example .env
nano .env

# Subir container
docker compose up -d --build

# Nginx
sudo cp nginx.conf /etc/nginx/sites-available/nexo
sudo ln -s /etc/nginx/sites-available/nexo /etc/nginx/sites-enabled/nexo
sudo nginx -t && sudo systemctl reload nginx

# SSL
sudo certbot --nginx -d nexo.dsmsys.com.br
```

### 3. Frontend PWA
```bash
cd nexo-pwa
cp .env.example .env
nano .env   # preencher VITE_API_URL e chaves Supabase

npm install
npm run build
# Deploy da pasta dist/ em Vercel, Netlify ou nginx
```

### 4. Jobs agendados (cron no servidor)
```bash
# Alertas internos — todo dia às 8h BRT
0 11 * * * cd /app && python -m jobs.alertas

# Alertas de mercado — toda segunda às 9h BRT
0 12 * * 1 cd /app && python -m jobs.alertas_mercado
```

### 5. Provisionar primeiro tenant (Designtex)
```sql
-- No SQL Editor do Supabase:
INSERT INTO tenants (cnpj, nome, perfil_mercado) VALUES (
  '00.000.000/0001-00',
  'Designtex Tecidos',
  '{
    "setor": "indústria têxtil",
    "nicho": "tecidos de algodão e malha",
    "insumos_chave": ["algodão", "poliéster", "fio têxtil"],
    "regiao_atuacao": "Brasil"
  }'::jsonb
);
```

---

## Onboarding de novo cliente (fluxo)

```
1. Contrato fechado → INSERT INTO tenants (cnpj, nome)
2. Pegar schema do banco do cliente
3. POST /nexo/onboarding/analisar (header: X-Admin-Key)
   → IA devolve mapeamento + perguntas ao integrador
4. Responder perguntas com o TI do cliente, corrigir mapeamento
5. POST /nexo/onboarding/gerar (mapeamento_revisado)
   → IA devolve as 10 RPCs SQL prontas
6. ⚠️ REVISAR o SQL e aplicar manualmente no banco
7. Testar: nexo_vendas_periodo vs relatório oficial → bateu? ✅
```

---

## Segurança em produção

| Item | Garantia |
|---|---|
| IA nunca inventa número | Banco calcula via RPC; IA só narra |
| Isolamento multi-tenant | 3 camadas: token → backend → RLS |
| Vendedor vê só o dele | `p_rep` injetado do token, nunca do usuário |
| service_role | Só no backend, nunca no front |
| CORS | Restrito a `nexo.dsmsys.com.br` |
| HTTPS | Certbot — renovação automática |
| Auditoria | Toda pergunta em `nexo_logs` |

---

## Roadmap — o que vem a seguir

1. **Filtro por setor** — além de vendedor, filtrar por departamento
2. **Export PDF/Excel** — relatórios para download
3. **Relatório agendado** — resumo automático no e-mail toda segunda
4. **Cache** — Redis para perguntas idênticas no mesmo dia
5. **Pitch/demo script** — roteiro de 5 min para fechar contratos
