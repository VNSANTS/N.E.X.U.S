# N.E.X.U.S. local API and web app

## Install and start

Requirements: Python 3.11 or newer; runtime and tests use only the Python standard library. From the repository root:

```powershell
python -m unittest discover -s tests -v
python -m nexus_learning --db nexus_learning.db serve --host 127.0.0.1 --port 8765
```

On first run, the CLI prompts for a username and a password of at least 14 characters. Passwords are stored as PBKDF2-HMAC-SHA256 hashes with per-user random salt. No default password exists. Open `http://127.0.0.1:8765/`, log in, and use the web interface. Stop with Ctrl+C. The API is deliberately loopback-only; it has no TLS, and must not be exposed through port forwarding or a reverse proxy as-is.

The server persists data in `nexus_learning.db` (ignored by Git). Back up this database securely before upgrades. There are no destructive schema migrations; API tables are additive. Local browser tokens are kept in JavaScript memory and expire after 12 hours; logout revokes the token. Failed logins are rate-limited in-process.

## API authentication

`POST /api/v1/auth/login` accepts `{"username":"...","password":"..."}` and returns an opaque bearer token. All other API routes except `/api/v1/health` require `Authorization: Bearer <token>`. Sessions and runtime tasks are always queried through the authenticated user ID; a session ID is not authorization. Request JSON is limited to 64 KiB. The API verifies loopback Host and same-origin requests, does not enable CORS, and returns no-store JSON responses.

## Endpoints

| Method and path | Behavior |
|---|---|
| `GET /api/v1/health` | Local process health. |
| `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `POST /api/v1/auth/logout` | Password login, identity and token revocation. |
| `GET/POST /api/v1/sessions`, `GET/DELETE /api/v1/sessions/{id}` | List/create, inspect and delete owned sessions. |
| `GET/POST /api/v1/sessions/{id}/messages` | Read history or submit one synchronous chat turn. A failed generation still has an inspectable task. |
| `POST /api/v1/sessions/{id}/messages/stream` | Stream a chat turn as server-sent events; completed answers are persisted with actual provider/model metadata. |
| `GET /api/v1/tasks`, `GET /api/v1/tasks/{id}` | List/get owned runtime task states and audit events. |
| `GET/POST /api/v1/memories`, `DELETE /api/v1/memories/{id}` | Search/list or explicitly add/archive memory. Writes require `confirm: true`; assistant output is never written automatically. |
| `GET/POST /api/v1/sources` | List or register source metadata. Registering a URI does not fetch it. |
| `GET/POST /api/v1/claims`, `GET /api/v1/claims/{id}`, `POST /api/v1/claims/{id}/review` | Propose, inspect and explicitly review sourced claims. New claims start `proposed`; validation requires rationale and confidence. Writes require `confirm: true`. |
| `GET /api/v1/agents`, `GET /api/v1/agents/activity` | Specialist roster and server-sanitized `agent.llm_*` metadata for the authenticated owner. Prompt text, model responses and tool results are excluded. |
| `GET /api/v1/activity` | General redacted task activity for the authenticated owner. |
| `GET /api/v1/tools`, `POST /api/v1/tools/{id}/execute` | Tool catalog and bounded allowlisted READ tools only. No shell, code execution, remote MCP or sensitive tool exists. Unknown tools are denied. |
| `GET/POST /api/v1/jobs`, `GET /api/v1/jobs/{id}`, `GET /api/v1/jobs/{id}/events`, `POST /api/v1/jobs/{id}/cancel`, `POST /api/v1/jobs/run-once`, `GET /api/v1/worker/status` | Durable local jobs with idempotency keys, priority, optional one-shot `run_after`, leases and bounded retries. Cancellation is for queued work; status reports the last worker heartbeat. |
| `GET /api/v1/config` | Active provider/model; never returns secrets. |
| `GET /api/v1/providers`, `GET /api/v1/providers/{provider}/models`, `POST /api/v1/providers/{provider}/check`, `POST /api/v1/providers/default` | Provider availability, model discovery, explicit connection test and persistent model selection. |
| `GET /api/v1/integrations`, `GET /api/v1/integrations/usage`, `POST /api/v1/integrations/check` | Configuration, daily counters and explicitly confirmed connectivity checks. Gemini/Tavily checks can consume quota/credits. |
| `POST /api/v1/integrations/check` with Gemini/Tavily validates credentials without model generation or a search; `POST /api/v1/integrations/tavily/search`, `POST /api/v1/integrations/tavily/extract`, `GET /api/v1/integrations/documents` | Confirmed web search/extraction, source registration, untrusted document archive. |
| `GET/POST /api/v1/integrations/github/repos`, `POST /api/v1/integrations/github/repos/{id}/sync` | Track public repositories and sync read-only metadata/commits/issues. |
| `GET /api/v1/usage`, `GET/POST /api/v1/usage/budget` | Provider usage and explicit fail-closed daily/per-task budget. |
| `/api/v1/learning/settings`, `/topics`, `/cycles`, `/findings`, `/research`, `/questions` | Persistent bounded learning and owner review endpoints; see [CONTINUOUS_LEARNING.md](CONTINUOUS_LEARNING.md). |

Conversation turn example after login:

```json
{"content":"O que registrei sobre o projeto?"}
```

### Skills management (owner review required)

| Method and path | Behavior |
|---|---|
| `GET /api/v1/skills?query=...` | Search only approved text-only skills using literal, case-insensitive substring matching. |
| `GET /api/v1/skills/proposals` | List up to 20 pending proposals, including full instruction text for owner review. Requires authentication. |
| `POST /api/v1/skills` | Propose a versioned text-only skill. New proposals are pending and are not loaded into chat. |
| `POST /api/v1/skills/{id}/approve` with `{"confirm":true}` | Explicitly approve a pending proposal; writes an audit event. |
| `POST /api/v1/skills/{id}/reject` with `{"confirm":true}` | Explicitly reject a pending proposal; writes an audit event and removes it from the pending queue. |

The Skills screen shows the full instructions before approval/rejection. Skills are untrusted text and cannot grant tools, permissions or code execution. Approved content is checked against its stored SHA-256 hash when loaded.

## Providers

The provider manager supports Ollama, OpenAI, Anthropic, Google Gemini, Groq, OpenRouter and MockProvider. The code default without a local setting remains MockProvider for development; the local `.env` supplied with this checkout selects Ollama and `qwen2.5:0.5b`. Provider selection is persisted in `provider_settings`, so changing `.env` does not override a database selection that already exists. Use the authenticated provider settings screen or `POST /api/v1/providers/default` to change it.

Ollama is restricted to loopback HTTP. The manager queries `/api/version`, `/api/ps` and `/api/tags`, auto-suggests the smallest installed Qwen model, and never downloads a model. The adapter streams `/api/chat` NDJSON, preserves recent conversation history, allows cancellation by closing the request, and returns an explicit error if the selected model is missing. Context, generation length, temperature and timeout are set through `OLLAMA_NUM_CTX`, `OLLAMA_NUM_PREDICT`, `OLLAMA_TEMPERATURE` and `NEXUS_PROVIDER_TIMEOUT`. A working connection does not guarantee answer quality; the installed 0.5B Qwen model has produced inconsistent answers in simple reasoning checks.

Remote providers require `NEXUS_ENABLE_REMOTE_PROVIDER=true`, a provider key and model in the local `.env`, and an explicitly enabled provider budget in the authenticated UI. Set `NEXUS_REMOTE_PROVIDERS=gemini` to restrict this opt-in to Gemini. Keys stay in the backend and are never returned by provider status. MockProvider is for development/tests and is not a silent fallback when a real provider fails. Gemini authentication and model discovery were verified with the real key using the models-list GET only; the configured `gemini-2.5-flash` is available. No generation request was made, and the provider budget remains disabled. Tavily authentication was verified through `GET /usage`, which reports account/key counters without spending search credits. No real search was run; each search requires user confirmation and can consume credits.

### Optional multi-agent conversation stage

`NEXUS_MULTIAGENT_ENABLED=false` is the default. Set it to `true` locally to run the bounded Architect → Analyst → Reviewer sequence before the final answer for requests classified as ADVANCED or RESEARCH. By default each role uses the selected main provider/model; optional per-role `NEXUS_AGENT_MODELS` overrides may select separate providers/models. Each role makes up to one generation call; all agents have no tools. Results are size/schema validated, marked as untrusted data in the final prompt and excluded from logs. Remote runs first check that the configured budget can accommodate three specialist calls plus the final answer, then each call passes through the normal atomic budget gate. The preflight itself is not an all-or-nothing reservation, so concurrent usage or a budget change can make later stages stop after earlier calls have consumed budget. Leave this feature disabled if you do not want the additional inference calls.

`GET /api/v1/providers` returns configured state, actual local Ollama availability, installed and loaded models, and the persisted selection without secrets. `GET /api/v1/providers/{provider}/models` lists models; `POST /api/v1/providers/{provider}/check` performs an explicit connection check with `{"confirm":true}`; Gemini checks use model discovery, not generation; `POST /api/v1/providers/default` selects an installed model with `{"provider":"ollama","model":"qwen2.5:0.5b","confirm":true}`. The web UI uses these endpoints.

## Worker and agent behavior

Run `python -m nexus_learning --db nexus_learning.db worker --poll 1` in another terminal or use `scripts/run-worker.ps1`. It processes allowlisted stats, consolidation and one bounded learning-cycle phase per job. The worker is single-threaded. Lease tokens fence stale workers; retry attempts and cycle recovery are bounded. Recurrence only runs while the worker is active; no cloud worker is implemented.

Product agents are not the six Codex development profiles. The product supervisor delegates deterministic memory retrieval and request classification with structured activity records and one-step limits. Cycles can call Crossref metadata and optionally Tavily when environment and per-topic opt-ins and limits are satisfied. The reviewer checks response shape, not factual truth. This is a supervised foundation, not autonomous specialist model collaboration.

## Current limitations and deployment checklist

- Local API only and single-process WSGI server. No production deployment, TLS, remote identity provider, password reset or multi-user memory partition. Streaming chat is implemented; active Ollama generation is cancelled when the stream closes, while cancellation behavior of remote adapters depends on their HTTP transport.
- The first and only owner account is created interactively; the database trigger rejects a second local account. There is no public sign-up endpoint. Sessions/tasks are still owner-filtered defensively; memories, sources, claims and aggregate learning jobs remain single-owner data.
- Memory retrieval is lexical, bounded to 3,500 characters and uses active memories plus claims in `validated` state with source records. Retrieved content is labeled untrusted. Model responses remain conversation history only.
- Before remote exposure: select hosting, TLS/reverse proxy, identity/session policy, database backups, retention/deletion, rate limits, secret manager, CSRF/browser threat model and monitoring; then add deployment-specific security tests. Do not expose this development server to LAN/Internet.


## Continuous intelligence and external integrations

Read [CONTINUOUS_LEARNING.md](CONTINUOUS_LEARNING.md) for cycle operation and [INTEGRATIONS.md](INTEGRATIONS.md) for Gemini, Tavily, Crossref, GitHub, local secrets and explicit budgets. External search is off by default; content from the web and repository metadata are untrusted data.

## Continuity - ALL FOR ONE / initial routing (2026-11-01)

- Audit confirmed that chat provider selection remains manually persisted; automatic model routing is not yet connected to chat runtime.
- Added `nexus_learning/model_router.py`: pure deterministic policy for SIMPLE, STANDARD, ADVANCED and RESEARCH; filters availability, capability, context, cost and latency metadata; fallback stays within local/remote trust boundary.
- Fail-closed behavior: remote candidates require explicit remote permission and budget authorization; unavailable, disallowed, malformed or insufficient-context candidates are rejected.
- This policy is not yet wired into runtime provider choice. Model latency, price and capability metadata need a trusted catalog or reviewed configuration before automatic routing. Manual Ollama/Qwen selection remains unchanged.
- Product-agent roles remain sequential and deterministic, not independent LLM agents. Research, knowledge and memory infrastructure exist, but chat does not delegate model tool calls. No Gemini generation or Tavily search was run during this work.
- Initial integrity audit found numerous existing local changes; all preserved. `.env` and local database remain Git-ignored. No commit/push. Codex profiles passed static validation, but subagent startup failed because the local OAuth token had been invalidated after the user's logout; no global settings were changed.
- Verification: `python -m compileall -q nexus_learning tests` passed; `python -m unittest discover -s tests -v` passed with 97 tests, including 9 router tests; `git diff --check` passed.

## Conversational research and routing

`POST /api/v1/sessions/{id}/messages` and `/messages/stream` classify a bounded set of research/current-information requests. If Tavily is enabled and configured, an unconfirmed request returns HTTP 409 with `code: research_confirmation_required`; it does not persist the user message or invoke Tavily. Retry with the same content and `confirm_research: true` to authorize one bounded basic search. The result includes `sources`; SSE `done` includes the same field. A disabled/unconfigured integration returns 503. Research history is available from `GET /api/v1/sessions/{id}/research` and is scoped to the authenticated owner.

The UI makes this confirmation explicit and renders returned source URLs as external links. Search results are untrusted input and are never treated as privileged instructions.

`GET /api/v1/providers` includes a safe routing summary. `NEXUS_ROUTING_MODE=manual|automatic` controls selection; automatic mode additionally requires a reviewed `NEXUS_ROUTER_CANDIDATES` JSON catalog. Remote candidates require existing remote-provider opt-in and an enabled bounded inference budget.
## Tool call capability gate

Set NEXUS_TOOL_CALLING_MODELS in local .env only after verifying native tool support for the exact selected model. The API accepts comma-separated provider:model identifiers. The default is empty. Available schemas are READ-only (memory.search, knowledge.claims); sensitive research is not included. Remote continuations remain behind the provider budget and count as separate calls. Tool calls currently use the synchronous messages endpoint; the SSE route keeps streaming and cancellation and withholds tools until cancellable generation transport is available. Full details: docs/UNIVERSAL_TOOL_CALLING.md.


## Modelos independentes para especialistas

O estágio multiagente continua desativado por padrão. Para ativá-lo, configure `NEXUS_MULTIAGENT_ENABLED=true`. Opcionalmente, use `NEXUS_AGENT_MODELS` como objeto JSON com um provider/model por papel:

```dotenv
NEXUS_MULTIAGENT_ENABLED=true
NEXUS_AGENT_MODELS={"architect":"ollama:qwen2.5:0.5b","analyst":"gemini:<model-id-verificado>","reviewer":"ollama:qwen2.5:0.5b"}
```

Papéis aceitos: `architect`, `analyst` e `reviewer`. O formato de cada valor é `provider:model`; modelos não configurados continuam usando o provider principal. O `ProviderManager` exige credenciais presentes, opt-in remoto e allowlist para cada provider remoto. Chamadas remotas entram no preflight de orçamento e cada geração continua fazendo sua própria reserva. Se o orçamento não autorizar o conjunto remoto, o pipeline é bloqueado antes da primeira chamada.

A configuração não faz descoberta de modelos nem uma chamada de saúde automática: informe apenas IDs conhecidos/verificados. Nesta etapa, falha de um modelo de especialista encerra a pipeline em vez de repetir uma chamada potencialmente faturável. Fallback entre modelos, mesmo dentro do mesmo trust lane, ainda é pendência. Os especialistas continuam sequenciais, sem ferramentas próprias e sem execução de código.


## Auditoria estruturada de evidências dos especialistas

O pipeline pode transportar claims tipadas em cada deliverable: texto da afirmação e `evidence_ids`. Quando fontes são fornecidas, o runtime atribui IDs locais `S1`–`S3` e rejeita IDs que não existam no catálogo recebido ou que estejam duplicados. O estado resultante é apenas `source_linked` ou `unreferenced`; não existe pontuação numérica automática de confiança nem declaração de que a fonte prova a afirmação.

As fontes são dados não confiáveis. Um ID válido só indica que o modelo referenciou um item que foi incluído no contexto. Não garante qualidade, atualidade, independência ou veracidade. A revisão semântica do Reviewer continua sendo uma etapa de modelo, não uma verificação factual independente.

O orçamento configurado usa preços estimados globais, não tarifários por modelo. Em uma execução com vários providers remotos, configure os preços por milhão de tokens de forma conservadora, considerando o modelo mais caro selecionado; o preflight é uma estimativa e não substitui limites de faturamento do provedor.


Na síntese final, quando o pipeline recebe fontes, a API omite as claims `unreferenced` de forma determinística e registra a quantidade omitida em cada deliverable. O texto do contexto diferencia `source_linked` de verificação factual: resumo e itens continuam não confiáveis; links não provam a verdade de uma afirmação. Sem fontes, claims ficam rotuladas como `unreferenced` e a síntese recebe instrução para não tratá-las como fatos.


## Limite global do pipeline de especialistas

A pipeline sequencial tem um prazo global padrão de **90 segundos** (configurado internamente, máximo permitido de 180 segundos). Cada chamada recebe o menor valor entre o timeout por chamada e o tempo restante. Se uma chamada ultrapassar o prazo, a execução é marcada como `pipeline_timeout`, as etapas seguintes são marcadas como ignoradas e a síntese final não é chamada. O adaptador recebe um timeout reduzido, mas o limite efetivo depende de o transporte HTTP/provedor respeitar esse timeout; nenhuma interrupção forçada de código externo é simulada.


Skill discovery uses literal case-insensitive text matching rather than SQL wildcard semantics. API search terms containing '%' or '_' are treated as ordinary text. Internal selection limits are strict: at most 10 skills and 12,000 total instruction characters; invalid numeric types, negative values and oversized values are rejected. Approved skill instructions are hash-checked on every load.


### Revisão estruturada por claim

O Reviewer produz uma avaliação por claim do Analyst usando índice zero-based, status `supported`, `unsupported`, `uncertain` ou `conflicting` e nota de até 60 caracteres. A API valida cobertura 1:1; avaliações ausentes, duplicadas ou fora do intervalo falham. `supported` sem evidência fornecida é rejeitado. Reviewer não cria claims novas nesse estágio.

Na síntese, claims `unsupported` e `conflicting` são removidas de forma determinística, mesmo sem exigir source filtering. Claims `uncertain` continuam identificadas. Eventos metadata-only indicam se o Reviewer usou provider/model diferente do Analyst. Essa diversidade não comprova veracidade e não substitui revisão humana.


### Atividade dos agentes na interface

`GET /api/v1/agents/activity` retorna no máximo 60 eventos `agent.llm_*` da conta autenticada. A resposta contém somente metadados permitidos: agente, provider/model, estado, duração, contagens de caracteres, código de erro, motivo, task ID e indicador de modelo distinto do Reviewer. Prompts, saídas dos modelos, resultados de ferramentas e eventos de outras contas são excluídos no servidor.


The Agents screen uses the sanitized `GET /api/v1/agents/activity` route rather than the general activity feed. The server returns at most 100 specialist LLM events for the authenticated owner and filters event details through an allowlist. It does not return prompts, model response text, retrieved context, tool arguments or tool results. Individual tool-call activity has not yet been added to this screen.
