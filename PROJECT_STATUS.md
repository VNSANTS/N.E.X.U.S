# Project Status

## Current remote snapshot — 2026-11-02

- **Published source:** branch `nexus/review-nov-02`, commit `16991c3aaf030f2ff9ef9233b61253c100a82538`. This is a review branch; it is not merged into `main`.
- **Verified at publication:** local Codex reported 183 unit tests passing, 5 optional E2E tests skipped, `compileall` passing and `git diff --check` passing. GitHub Actions had not yet run for this commit.
- **Application state:** authenticated local Python/SQLite WSGI app with browser UI, contextual memory, research confirmation, bounded worker, provider routing and allowlisted READ tool calling. It is not cloud-hosted and remains loopback-only; the PC can be off while the repository is reviewed, but the app itself is not remotely accessible.
- **Providers:** native bounded tool-call adapters exist for Ollama, OpenAI-compatible providers, Gemini and Anthropic. Validation used mocks; no real provider generations or external searches were made in the published round. SSE deliberately withholds model tools while preserving cancellation.
- **Skills:** registry/API, proposal and explicit approval, version/hash integrity checks, relevant on-demand loading and injection into synchronous and SSE chat are implemented. Skills remain untrusted text and cannot grant tools or permissions.
- **Specialists:** Architect → Analyst → Reviewer pipeline is opt-in, sequential, bounded, tool-less and metadata-audited. In the published commit all specialists use the same selected provider/model. Independent model selection, structured evidence verification and stronger delegation are still pending in that published snapshot.
- **Not production-ready:** no cloud deployment/TLS, remote worker, multi-user isolation, safe code-execution sandbox, automated backup/restore or completed operational monitoring. Do not expose the local API to the public internet.
- **Secrets:** `.env`, local databases and logs were excluded from Git. The published tree passed a pattern scan for common credential formats; that scan is not a guarantee that every secret format is absent.

## Active remote continuation — 2026-11-02

- Working branch: `nexus/remote-continuation`; PR #3 targets `nexus/review-nov-02`, not `main`.
- `NEXUS_AGENT_MODELS` supports independent provider/model configuration for Architect, Analyst and Reviewer. ProviderManager preserves remote opt-in, allowlist, credential and budget controls. No automatic model capability/health discovery or fallback after ambiguous provider failure exists yet.
- `GET /api/v1/skills?query=...` now filters approved skills from the URL query string; its regression test passed.
- Structured evidence claims are bounded and source IDs are validated. When sources are supplied, unreferenced claims are now removed deterministically before final synthesis and counted per agent. The Reviewer and final synthesis are instructed to flag unsupported assertions. A source ID proves only that the reference existed in supplied context, not that the source is accurate or the claim is true.
- Latest CI head `18347368767042b78cfa86e0617550928a8152c0`: 193 unit tests passed on Python 3.11, 193 passed on Python 3.12, and 5/5 Playwright/Chromium browser E2E tests passed. Compilation succeeded in both unit-test jobs.
- No real provider inference, Tavily search or paid API call is part of this remote work. The local app is still loopback-only and not deployed; switching off the PC does not make the app itself cloud-accessible.

The entries below are historical development snapshots. They must not override this current remote summary.

## Historical snapshot — earlier continuation (2026-11-02)
- Worker tests now cover competing independent processes, idempotent enqueue across processes, stale-token fencing, active lease renewal during long handlers, terminal expiry events, recovery after service reconstruction, and task/link transaction recovery.
- Browser E2E uses Playwright in a temporary Python environment with a temporary Chromium install; 4 tests cover login failure/success, main navigation, streaming/history/new session, logout/relogin, mobile navigation, topic/cycle creation and declining external research confirmation.
- E2E surfaced and fixed the learning page's shifted `listRows` arguments. Cycle answers now advance the idempotency generation, persist owner context into the checkpoint, and save consented memory atomically with the answer.
- Context retrieval applies the aggregate item bound and prioritizes validated sourced claims before semantic/lexical memories.
- Research recovery persists its outcome and sanitized provider failures before the cycle checkpoint. Restart recovery now preserves `failed`, `partial_failure`, `no_results`, and collected record IDs without storing provider error messages. Older reservation tables are migrated additively; provider/operation/error labels are allowlisted before persistence.
- The LLM specialist pipeline is connected to normal and SSE conversation endpoints behind `NEXUS_MULTIAGENT_ENABLED=false`. ADVANCED/RESEARCH calls run Architect → Analyst → Reviewer, then final synthesis; outputs are bounded/untrusted, there are no tools, and activity stores metadata only. Remote usage is preflighted and each request receives its existing budget reservation.
- Current local validation: compileall passed; standard discovery passed 162 tests (5 opt-in E2E tests skipped); Playwright/Chromium passed 5/5, including specialist-enabled conversation. No provider or external research calls. CI's Python 3.11/3.12 and E2E jobs have not run remotely; no local YAML parser is installed.
- Repository is on `main`, at `852131e52f454175c501e6f36bcea2c04a73e9e7`; `origin/main` matches (fetch completed, no merge needed).
- Baseline suite before this session: 119 tests passed; the post-change suite passed with 122 tests. This session added regression coverage for concurrent idempotent job enqueue, Unicode budget preflight, and disabled/stale budget authorization, fixing a reviewed race where a reservation could use stale settings after a concurrent disable/reduction.
- No live provider or research calls were made. The ignored local `.env` was checked only for selected non-secret switches/endpoint; secret values were not printed or included here. Database contents and `debug.log` were not read. Budget remains an estimated preflight/reservation mechanism; provider tokenization and billing can differ.
- The opt-in LLM pipeline performs three sequential calls on the selected provider/model for ADVANCED/RESEARCH tasks; specialists do not yet have independent model routing, tools, or persistent deliverable storage. Remote stages require a preflight plus per-call budget reservations; the preflight is not an atomic batch reservation. Deployment, TLS, and production multi-user isolation remain pending.

## Completed
- Skills inventory and documentary triage: 46 directories with `SKILL.md` confirmed; see [docs/skills/FINAL_AUDIT.md](docs/skills/FINAL_AUDIT.md).
- Runtime architecture v1 drafted in [ARCHITECTURE.md](ARCHITECTURE.md).
- Static remote audit of official OpenJarvis repository documented in [docs/audits/OPENJARVIS_AUDIT.md](docs/audits/OPENJARVIS_AUDIT.md).
- Executable MVP specification drafted in [docs/MVP_SPEC.md](docs/MVP_SPEC.md).

## Confirmed direction
- Personal AI assistant beyond a conventional chatbot.
- Cloud-first runtime accessible from phone/browser; local Ollama optional.
- Text first; voice and button activation later.
- Lightweight event-driven standby, not a continuous LLM reasoning loop.
- Modular monolith first; bounded agents/tools and multi-provider-ready gateway.
- Separate personal memory and sourced knowledge.
- Learning through research, validation and evaluated workflows.
- Explicit approval for sensitive actions; sandboxed self-improvement.

## Current MVP proposal
- Authenticated text API and responsive web interface.
- One cloud model provider.
- Bounded orchestrator and one safe READ tool.
- Deterministic allowlist/policy, timeouts, budgets and structured logs.
- SQLite first; no vector database.
- Automated offline tests for success, failure, timeout, injection, access isolation and secret leakage.
- No voice, scheduler, parallel agents, shell/code execution, remote MCP or sensitive actions in MVP.

## OpenJarvis audit
- Official upstream: https://github.com/open-jarvis/OpenJarvis
- Commit reviewed: `570d75425d50592d931bac7a17ce6b2621561c06`.
- Declared license: Apache-2.0; manifest Python `>=3.10,<3.14`.
- Static review only; no clone, install, execution or tests performed.
- Recommendation: reuse selected interfaces/patterns only after local validation; do not replace the N.E.X.U.S. repository or modify upstream.

## Environment constraints
Development PC reported: Intel i5 first generation, 8 GB DDR3 RAM, HDD. Avoid requiring large local models. Provider and hosting costs remain undecided.

## Next milestone
Exercise the local app manually with fictitious data, then decide whether to enable one provider after reviewing cost, quotas, privacy, protocol and Brazilian Portuguese quality. The adapters now exist but remain disabled by default. Before any remote exposure, select hosting, TLS, production identity, retention and database recovery. The separate local OpenJarvis checkout matches the audited commit but has pre-existing modifications; review them before any OpenJarvis validation or reuse.

## Open risks
- The local OpenJarvis checkout matches the audited commit but contains two unreviewed local modifications; do not overwrite them, and review before testing or reuse.
- OpenJarvis security capabilities require deliberate profile/configuration; do not rely on permissive defaults.
- Cloud inference and hosting can create recurring costs.
- Public repository: never commit secrets, private conversation exports, credentials or personal records.

## Local verification — 2026-11-01
- Environment: Windows, PowerShell 5.1, Git 2.55.0, Python 3.13.17, Codex CLI 0.164.0.
- `python -m compileall -q nexus_learning tests`: passed.
- `python -m unittest discover -s tests -v`: 28 tests passed locally (Python 3.13.17). The regression test for truthy non-boolean policy approvals was also run separately and passed after the fix.
- CLI help, `runtime-once` with MockProvider, TXT/Markdown ingestion, lexical search and SQLite persistence passed using a temporary database and fictitious Markdown fixture; temporary artifacts were removed.
- Corrected fail-closed policy handling so only literal `True` is an approval and `allow_reversible` must be a boolean. Added regression coverage.
- Added ignore rules for local logs, backups and temporary files. The pre-existing untracked `debug.log` was not opened or changed and now matches the log ignore rule.
- Updated the README summary and next step to match the implemented offline prototype and current provider decision gate.
- This local change has not been run in GitHub Actions. No remote fetch was performed because the checkout contained the pre-existing untracked `debug.log` before work began.
- Project Codex profiles/configuration are present and TOML-valid, but this checkout's explicit trust status and profile loading were not confirmed. No user-level trust settings were changed.

## Provider readiness and architecture audit — 2026-11-01
- Completed official-source comparison for Gemini, Groq and OpenRouter in [docs/PROVIDER_EVALUATION_2026-11-01.md](docs/PROVIDER_EVALUATION_2026-11-01.md). No provider was selected; exact quotas/terms can change and Brazilian Portuguese quality requires a controlled benchmark.
- At the earlier audit checkpoint, only stable provider-neutral error types had been added; this subsequent application implementation adds opt-in adapters, with no credentials, automatic retry/fallback, or real provider network calls. MockProvider remains the default.
- Runtime, memory and Codex multiagent findings and proposed infrastructure sequence: [docs/RUNTIME_MEMORY_AND_MULTIAGENT_AUDIT.md](docs/RUNTIME_MEMORY_AND_MULTIAGENT_AUDIT.md).
- Existing memory/source/claim/audit/task modules are implemented locally, but contextual memory retrieval and conversation sessions are not integrated. Model outputs are not promoted to facts.
- Six project profile TOMLs parse with unique names; project config enables at most four concurrent threads. This session loaded AGENTS.md, but custom profile activation and trust inheritance remain unconfirmed. No global Codex settings changed.
- This checkout had pre-existing local modifications before this work; they remain preserved. `debug.log` was not read, modified or removed, and the separate OpenJarvis checkout remains untouched.

## Local application slice — 2026-11-01
- Added authenticated loopback-only WSGI API and responsive web app; interactive first-owner setup has no default password. Passwords use PBKDF2-HMAC-SHA256 and API tokens are opaque, hashed at rest, expire after 12 hours, and can be revoked at logout.
- Sessions/messages persist in SQLite and are owner-scoped. Chat retrieves bounded active memories and validated claims with source excerpts before generation. Model output is conversation history only.
- Added explicit memory/source/claim operations, with confirmation for memory/claim writes and reviews. Knowledge claim creation remains `proposed`; validation remains explicit and audited.
- Added deterministic supervised product-agent delegation for memory retrieval and request classification. The other listed roles are rostered; this is not general LLM-to-LLM collaboration. The reviewer checks response shape only.
- Added two READ tools (`memory.search`, `knowledge.claims`) behind strict schemas and fail-closed policy; no shell, code execution or sensitive executor exists.
- Added durable local worker queue, priorities, one-shot schedule (`run_after`), idempotency keys, single-thread handler allowlist, lease fencing, bounded retries, cancellation of queued jobs and activity history. Run the worker as a separate process.
- Added standard-library Gemini, Groq and OpenRouter adapters. MockProvider remains default; remote use requires `NEXUS_ENABLE_REMOTE_PROVIDER=true`, explicit provider/model and key variables. No credentials or real provider requests were used.
- Detailed endpoints, configuration and deployment limits: [docs/LOCAL_API.md](docs/LOCAL_API.md). Provider selection remains undecided.
- Final local validation after this implementation: compileall passed; all 47 unittest cases passed on Python 3.13.17; CLI/serve/worker help and `git diff --check` passed. CI was not run.
- The local auth store enforces one owner account with a database trigger; jobs are also scoped by owner. This makes the existing global learning-memory tables safe for the current single-owner product shape. Multi-user support would require ownership columns and filtered retrieval for all memories/sources/claims.
- Final suite includes the single-owner and job-scope checks. No CI run.


## Atualização de arquitetura — cloud core + PC worker
A decisão mais recente é uma arquitetura híbrida para um único usuário:
- **Nuvem:** núcleo leve, interface, API, autenticação, conversas, memória essencial, orquestração, fila e cache compacto de conhecimento validado. Deve continuar acessível com o PC desligado.
- **PC:** armazenamento ampliado e pipeline pesado de aprendizado/pesquisa (ingestão, extração, limpeza, deduplicação, indexação e comparação de evidências).
- **PC offline:** tarefas locais aguardam em fila; a nuvem continua disponível com contexto mínimo e conhecimento validado sincronizado.
- **Segurança:** worker inicia conexão autenticada de saída; sem shell remoto ou porta pública.
- **Custo:** meta de R$ 0 obrigatório, usando planos gratuitos e sem cobrança automática, sujeito a cotas e termos.
- **Limite local:** i5 de primeira geração, 8 GB RAM e HDD; processamento em lotes pequenos, sem modelos locais grandes como requisito.

Esta é uma decisão de arquitetura/documentação, não uma implementação. Ver a revisão v2 em ARCHITECTURE.md e D-014 em DECISIONS.md.


## Atualização — modelo local auxiliar
Foi aceita a direção de usar, no PC, um modelo local pequeno e substituível como auxiliar do aprendizado: resumir, classificar, extrair candidatos e organizar documentos. Ele não será considerado fonte de verdade nem poderá validar sozinho suas próprias conclusões. O pipeline preservará fontes, evidências, incertezas e revisão. Tarefas difíceis poderão usar a IA na nuvem dentro das regras de privacidade e cotas. A viabilidade de modelos no i5 de primeira geração/8 GB RAM ainda precisa ser medida no PC; não há modelo escolhido ou instalado. Ver D-015 e a revisão v3 de ARCHITECTURE.md.


## Pesquisa aplicada à arquitetura de aprendizado
Criado `docs/LEARNING_ARCHITECTURE_NEUROSCIENCE.md`, com síntese de literatura, distinção entre consenso/debate/proposta de engenharia, arquitetura em camadas, estados de conhecimento, proteções contra aprendizagem incorreta, métricas e fases compatíveis com hardware limitado. O documento é especificação/proposta; não significa que o motor de aprendizado já foi implementado.


## Primeiro código do motor de aprendizado

**Implementado no repositório (núcleo inicial):**
- pacote Python `nexus_learning` com persistência SQLite;
- três categorias de memória;
- registro de fontes e afirmações candidatas vinculadas a fontes;
- estados de validação com justificativa obrigatória e confiança explícita para validação;
- fila de tarefas com prioridade heurística explicável;
- testes `unittest` cobrindo separação de memória, validação explícita e ordenação de tarefas.

**Ainda não verificado neste ambiente:** execução dos testes, compatibilidade com a versão Python instalada no PC e comportamento sob uso prolongado. O código foi enviado ao GitHub, mas não foi executado no computador do usuário.

**Ainda não implementado:** ingestão automática de arquivos/web, comparação semântica avançada, consolidação em background, LLM local/nuvem, API, interface, autenticação, worker, sincronização e deploy. Não chamar o sistema de assistente funcional completo nesta etapa.


## Expansão do núcleo executável — 2026-10-31

Adicionados ao pacote local:
- pesquisa e arquivamento de memórias;
- consulta de afirmações e suas fontes/excertos;
- revisão de estado com justificativa obrigatória;
- relatório de consolidação que detecta candidatos a duplicata e afirmações sem fonte, sem alterar registros;
- estados de tarefas e log de auditoria;
- interface CLI ampliada;
- testes de regressão adicionais;
- workflow do GitHub Actions para executar testes em Python 3.11 e 3.12;
- `.gitignore` para bancos locais e artefatos Python.

**Verificação:** o workflow foi configurado, mas o resultado de execução do GitHub Actions ainda precisa ser conferido. Não afirmar que os testes passaram até haver resultado verde. O código também ainda precisa ser executado no PC local.


## Ingestão de documentos — protótipo inicial

Adicionado `nexus_learning/ingestion.py`:
- ingestão de texto/Markdown por API Python e CLI;
- limite padrão de 1 MB e lista explícita de extensões;
- normalização básica, hash SHA-256 e detecção de conteúdo duplicado;
- divisão em trechos com índices e posições no texto;
- busca lexical simples com referência à fonte original;
- testes para proveniência, duplicatas, limites e configuração de trechos.

**Limites:** não lê PDF/DOCX, não navega na web, não faz OCR, não extrai afirmações automaticamente e não usa embeddings/LLM. A busca é lexical. Os testes foram escritos, mas ainda precisam de execução confirmada no GitHub Actions e no PC local.


## Runtime controlado — protótipo adicionado

- `nexus_learning/policy.py`: autorização fail-closed e allowlist para classes READ, WRITE_REVERSIBLE e SENSITIVE.
- `nexus_learning/providers/`: contrato independente de provedor e MockProvider offline.
- `nexus_learning/runtime.py`: ciclo de tarefa conversacional persistido em SQLite, com eventos e registro de falha.
- `runtime-once`: smoke test manual usando o provedor simulado.
- `tests/test_runtime.py`: testes para política e runtime.
- `CODEX_HANDOFF.md`: instruções e critérios para concluir integração local via Codex CLI.

**Ainda não implementado:** adaptador real de IA, API HTTP, autenticação, execução de ferramentas, worker cloud/PC, sincronização, agendamento, notificações e implantação. O MockProvider não é um modelo de IA. **CI confirmado:** o workflow executou com sucesso os testes em Python 3.11 e 3.12 após a inclusão do runtime e do comando `runtime-once` (execução associada ao commit `ec1b6fd`). As atualizações posteriores foram apenas de documentação.


## Revisão de código e endurecimento — 2026-10-31

Foi feita uma nova inspeção do tree e dos módulos Python do repositório. O estado real permanece: motor SQLite, ingestão TXT/Markdown, pesquisa de metadados Crossref, política fail-closed, runtime textual com MockProvider e CLI local; ainda não há provider remoto, API, autenticação, interface web, worker cloud/PC ou deploy.

Correções gravadas nesta revisão:
- `:memory:` agora usa SQLite compartilhado com conexão âncora, pois o engine abre conexões por operação.
- Runtime reivindica tarefas com atualização condicional sob transação de escrita.
- Exceções de providers não são persistidas com a mensagem original, evitando gravar acidentalmente URLs, cabeçalhos ou credenciais.
- Validação dos limites do runtime e dos identificadores do modelo/provedor.
- Testes de regressão específicos adicionados.
- Workflow corrigido para observar seu próprio caminho, com permissões mínimas, timeout e compileall.

**CI confirmado:** a execução [41255344883](https://github.com/VNSANTS/N.E.X.U.S/actions/runs/41255344883) passou em Python 3.11 e 3.12, incluindo compileall e toda a suíte unittest, no commit de código `59356b7674ee97b9c2357871d2221e35f7e53b59`. O checkout e os testes no computador local ainda precisam ser executados.

O backlog operacional foi criado em `docs/IMPLEMENTATION_BACKLOG.md`. O próximo bloqueio técnico para a primeira conversa com IA real é escolher o provedor, protocolo, armazenamento de credenciais e limites. API/autenticação e hospedagem continuam decisões posteriores, não implementações presumidas.

## Continuidade - autonomia e integracoes (2026-11-01)

- Ciclo persistente de dez fases com fila, limites, checkpoints, recuperacao automatica limitada, pausa/retomada/cancelamento, perguntas ao proprietario e painel conectado a API. Recorrencia exige worker ativo e autonomia habilitada.
- Papeis internos: orchestrator, researcher, analyst, architect, developer, reviewer e knowledge_manager. Execucao sequencial e auditavel; nao sao agentes LLM paralelos. Gemini pode analisar resultados dentro do orcamento.
- Crossref e Tavily geram registros com proveniencia e classificacao nao confiavel; GitHub consulta repositorios, commits e issues apenas por GET. Contradicoes e atualidade sao heuristicas candidatas, sem validacao automatica de fatos.
- Gemini embeddings e indice vetorial local sao opcionais; indexacao e explicita e a recuperacao semantica cai para busca lexical.
- Providers remotos usam orcamento fail-closed diario e por tarefa (chamadas, tokens e USD). Precos configurados pelo proprietario; erros incertos conservam reserva.
- Verificacao final: compileall passou; a suite completa passou com 72 testes; integracoes foram simuladas e nenhuma chamada externa real foi feita.
- Registro historico da primeira configuracao: inicialmente nao havia `.env`; as chaves Gemini/Tavily foram posteriormente configuradas apenas no `.env` local ignorado pelo Git. GitHub continua sem token e em modo publico somente leitura. Consulte `docs/INTEGRATIONS.md`.
- Limites: API local loopback, worker local, Crossref metadata-only, Tavily sujeito a creditos, GitHub somente leitura; sem execucao de shell ou validacao automatica de conhecimento.


## Provider real e conversa streaming ? 2026-11-01

- Ollama 0.40.13 est? ativo em loopback e lista `qwen2.5:0.5b` (397 MB). A sele??o Ollama/Qwen foi confirmada no banco local consultando apenas `provider_settings`; nenhum conte?do de conversa foi lido.
- `OllamaProvider` implementa status/vers?o, modelos instalados/carregados, chat com hist?rico, limites de contexto/sa?da, temperatura, timeout, streaming NDJSON e cancelamento ao fechar o stream. Modelo ausente ? erro expl?cito; nenhum download/fallback ocorre.
- `ProviderManager` e API exp?em sele??o persistida, descoberta/teste e status sem credenciais; providers suportados incluem Ollama, OpenAI, Anthropic, Gemini, Groq, OpenRouter e MockProvider. Remotos seguem opt-in e or?amento expl?cito.
- Teste ponta a ponta real autenticou na API local, enviou turno SSE ao Ollama e confirmou persist?ncia do texto e metadados provider/model no hist?rico. Qwen 0.5B respondeu incorretamente ?3? a 2+2 em uma execu??o. A integra??o est? operacional, mas esse modelo n?o oferece qualidade confi?vel para racioc?nio; nenhuma troca ou download de modelo foi feita.
- Uma primeira execu??o da su?te encontrou duas falhas de teste; removidos os nomes de vari?veis de credencial da resposta do cat?logo e atualizada a expectativa do payload de temperatura. Testes direcionados passaram. Execu??o da su?te completa ap?s essas corre??es ainda pendente.
- Credenciais remotas n?o foram usadas. `.env` permanece local/ignorado; sem commit/push. `debug.log` e checkout OpenJarvis n?o foram acessados.


## Gemini e Tavily configurados localmente ? 2026-11-01

- As chaves foram gravadas apenas no `.env` local (ignorado pelo Git) com ACL restrita ao usuario Windows atual. Nenhuma chave foi inserida na documentacao, frontend, banco de dados, prompts ou logs. `NEXUS_REMOTE_PROVIDERS=gemini` restringe o opt-in remoto; Tavily esta habilitado para pesquisa manual confirmada, com aprendizagem recorrente desabilitada.
- Gemini autenticou via GET de listagem oficial de modelos; 46 modelos compativeis foram retornados e `gemini-2.5-flash` consta na lista. Nenhuma inferencia foi enviada; o orcamento de chamadas LLM continua desligado. Validacao final: 88 testes passaram; compileall e git diff --check passaram.
- Tavily autenticou via GET `/usage`; o endpoint reportou uso zero e limite de plano sem consumir creditos. Nenhuma pesquisa/extracao real foi disparada.
- O endpoint do N.E.X.U.S. `/api/v1/integrations/check` retornou ambos conectados sem gerar conteudo Gemini nem consumir busca. Selecionado no app continua Ollama/Qwen.
- Para utilizar Gemini em conversa, proprietario precisa selecionar o modelo e habilitar deliberadamente um orcamento na UI; chamadas podem gerar custo. Para pesquisar, usar a tela Integracoes e confirmar a consulta; ela pode consumir creditos.
- As chaves foram postadas em conversa. Como medida preventiva, recomenda-se rotaciona-las no Google AI Studio/Tavily apos substituir por novas no `.env`.

## Continuity - ALL FOR ONE / initial routing (2026-11-01)

- Audit confirmed that chat provider selection remains manually persisted; automatic model routing is not yet connected to chat runtime.
- Added `nexus_learning/model_router.py`: pure deterministic policy for SIMPLE, STANDARD, ADVANCED and RESEARCH; filters availability, capability, context, cost and latency metadata; fallback stays within local/remote trust boundary.
- Fail-closed behavior: remote candidates require explicit remote permission and budget authorization; unavailable, disallowed, malformed or insufficient-context candidates are rejected.
- This policy is not yet wired into runtime provider choice. Model latency, price and capability metadata need a trusted catalog or reviewed configuration before automatic routing. Manual Ollama/Qwen selection remains unchanged.
- Product-agent roles remain sequential and deterministic, not independent LLM agents. Research, knowledge and memory infrastructure exist, but chat does not delegate model tool calls. No Gemini generation or Tavily search was run during this work.
- Initial integrity audit found numerous existing local changes; all preserved. `.env` and local database remain Git-ignored. No commit/push. Codex profiles passed static validation, but subagent startup failed because the local OAuth token had been invalidated after the user's logout; no global settings were changed.
- Verification: `python -m compileall -q nexus_learning tests` passed; `python -m unittest discover -s tests -v` passed with 97 tests, including 9 router tests; `git diff --check` passed.

## Continuity update: router and confirmed chat research (2026-11-01)

- `ModelRoutingService` is now called by synchronous and SSE chat. Manual mode remains default. Automatic mode verifies configured model candidates against live model lists and health, capability/context metadata, the remote opt-in and the fail-closed budget. Safe fallback stays in the same local/remote trust lane and streaming retries only before emitting output. Route, selected model, and fallback metadata are audited.
- Tavily can now be invoked from chat for requests classified as current research. The API responds with a confirmation prompt before any search or message persistence. After confirmation, it performs a bounded basic search, stores source provenance, labels results as untrusted context, returns source links, and records per-session research history. The UI asks before retrying and renders links with `noopener noreferrer`.
- `research.search` is registered as a sensitive tool. Tool execution still passes through `PolicyEngine`; the code supplies approval only after the explicit confirmation field. Tool arguments are schema-validated and activity is audited. The reviewer rejects research answers that omit citations or cite a source index outside the supplied result list.
- Contextual memory retrieval remains active; new chat responses are not automatically promoted to factual memory.
- Verification: full unittest discovery passed with 114 tests; `compileall` passed; real provider generations and Tavily searches were not performed in this continuation.
- Limitations: this is coordinator-side intent classification plus confirmation, not provider-native model tool-calling / tool-result continuation. Product agents remain a bounded deterministic pipeline, not independent LLM workers. Self-improvement isolation/proposal execution is not implemented. Automatic routing is opt-in and needs an explicit candidate catalog; remote spending remains disabled by default.

## Gemini/OpenAI provider validation — 2026-11-01

Gemini and OpenAI adapters use the existing provider contract and shared HTTP transport; provider selection remains with ProviderManager and automatic decisions with ModelRoutingService. The runtime keeps manual routing as the default and leaves remote inference budgets disabled. provider_from_env now enforces an explicitly configured NEXUS_REMOTE_PROVIDERS allowlist, closing a gate inconsistency with ProviderManager while preserving legacy behavior when no allowlist variable exists. Gemini/OpenAI adapter, SSE, manual selection/status, and OpenAI automatic routing paths are covered by mocked tests. No API key was read, no provider request was sent, and no credits were consumed. See docs/INTEGRATIONS.md for configuration, model discovery, official API links, and limitations.
## Continuidade de tool calling nativo (2026-11-02)

Foi implementado um ciclo limitado de chamadas de ferramentas para o runtime autenticado. O contrato ToolCall adiciona pedidos estruturados sem alterar a resposta textual de providers existentes. Ollama e adapters OpenAI-compatible normalizam pedidos e resultados; Gemini e Anthropic continuam explicitamente sem tool calling.

A API habilita o ciclo somente para pares exatos provider:model listados localmente em NEXUS_TOOL_CALLING_MODELS; a configuração está vazia por padrão. O runtime expõe somente ferramentas READ do registro (busca em memória pessoal e claims por estado). Tavily permanece SENSITIVE e usa o fluxo anterior de confirmação do proprietário. Cada chamada passa por schema, registro e PolicyEngine; há limites de 4 rodadas, 8 chamadas, 180 segundos, 8 KB de argumentos/resultados e reserva de orçamento por chamada remota. Resultados são marcados como dados não confiáveis e não entram no histórico persistido. Logs registram ferramenta/estado, sem argumentos ou conteúdo retornado.

O caminho SSE continua usando transporte streaming e cancelável; chamadas de ferramentas são deliberadamente desativadas nesse caminho enquanto o transporte HTTP síncrono não oferecer cancelamento em voo. No streaming, o usuário mantém resposta incremental e cancelamento; para modelos explicitamente habilitados, o endpoint síncrono pode executar ferramentas.

Validação desta fatia: novos testes offline exercitam schemas, execução API autenticada, continuidade do modelo, negação de tool sensível, limites, resultados extensos, parsing Ollama/OpenAI-compatible, IDs exclusivos e preservação do SSE. Não foram realizadas chamadas reais a providers nem Tavily. Consulte docs/UNIVERSAL_TOOL_CALLING.md.

Limites que permanecem: não existe sandbox de código/arquivos porque não há executor desse tipo; os papéis Architect/Analyst/Reviewer continuam sequenciais, usam o mesmo provider e não chamam ferramentas; Gemini/Anthropic ainda não têm protocolo nativo de tool calling; integração por streaming aguarda transporte cancelável e eventos de progresso da ferramenta em SSE.


## Evidence policy update — latest remote CI

- Structured claims are now filtered before final synthesis whenever source records are present: only claims with a reference ID supplied in the request are passed as explicitly source-linked claims; unreferenced claims are withheld and counted.
- The Reviewer is instructed to flag factual statements without supplied source IDs in review items. Source linkage still does not establish source reliability or truth; summaries/items are untrusted analysis.
- CI on the previous evidence-claims contract and browser fixture (commit `373a55e803269ad9489d6ea4b26ce228e7738965`) passed: 190 unit tests in Python 3.11, 190 in 3.12, and all 5 browser E2E tests. This new deterministic withholding policy is not yet validated by CI.


## Bounded delegation update — pending CI

- Specialist pipeline now has a global 90-second deadline (constructor accepts 1–180 seconds), passes each provider the remaining time, and turns an overrun into `pipeline_timeout`. Later specialists are marked skipped and no final synthesis is invoked after an overrun.
- The transport/provider must respect its timeout; this is not a forced process kill. Per-stage call remains bounded by existing provider timeout and the global deadline.
- New tests verify timeout bounds and that a slow first stage prevents later stage calls. CI for this delta is pending.


## Specialist execution deadline — validated by CI

- Global specialist pipeline deadline: 90 seconds default, constructor maximum 180 seconds. Each specialist gets the remaining time, capped by the existing per-call timeout.
- A stage that returns after the deadline is converted to `pipeline_timeout`; later specialists are skipped and final synthesis does not run.
- Latest CI commit `029389e9a7ff3781ca0ec00770e2f7eaf1585927`: 195 unit tests passed on Python 3.11 and 195 on Python 3.12; 5/5 Playwright/Chromium E2E tests passed; compilation succeeded.
- This timeout is cooperative through the provider transport's timeout parameter, not a hard process kill. Durable stage resume and same-trust-lane fallback remain unfinished.
