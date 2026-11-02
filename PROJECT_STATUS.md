# Project Status

**Stage:** local authenticated application with persistent learning cycles and read-only integration infrastructure implemented on Windows/Python 3.13.17 (2026-11-01). Remote credentials and real-service validation are absent; remote deployment and production identity remain pending.
**Implementation:** Python/SQLite learning core, local WSGI API, browser UI, session history, lexical context retrieval, offline MockProvider, opt-in standard-library provider adapters, read-only tool registry and bounded local task queue are implemented and covered by tests. This is not a production-ready or remotely hosted assistant.

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


## Reliability foundation — 2026-11-02

- Created development branch `dev/reliability-zero-cost-foundation` from the audited `main` commit `852131e52f454175c501e6f36bcea2c04a73e9e7`. Main remains unchanged.
- Removed the duplicate `ProviderBudget.can_reserve` definition.
- Added conservative UTF-8 byte-based text estimates and per-message framing allowance; used the shared estimator in provider accounting and automatic routing. These are safety estimates, not tokenizer-exact counts. Provider usage returned by a provider remains preferred when available.
- Expired 401 sessions now clear the stale browser `sessionStorage` token before showing login again.
- Added unit tests for estimator behavior and malformed input.
- Validation is pending GitHub Actions on this branch. No live provider calls, paid requests, deployment, or local-machine changes were performed.
- Remaining hardening: task-aware preflight accounting, provider-specific tokenizers/usage normalization, robust tests for browser session lifecycle, and per-claim citation support validation.


### Additional budget hardening — 2026-11-02

- The remote-provider budget now rejects non-integer, boolean, or negative token reservations before writing usage records.
- Routing preflight and the atomic reservation gate both fail closed when either configured model token price is zero or invalid, including legacy/corrupted settings.
- Added regression tests for corrupted zero output pricing and invalid token reservations. GitHub Actions is being re-run against the final branch head; the earlier successful run covered the preceding code revision, not these last regression tests.


### Phase 2 — Evidence quality foundation (2026-11-02)

- Added deterministic claim evidence assessment: linked source count, HTTP(S) URL validity, non-empty excerpt coverage, distinct-domain count, and explicit issue codes.
- Claim promotion to `validated` now requires every linked source to have a valid HTTP(S) URL and a non-empty excerpt. Claims with no source, local-only URI, or missing excerpts remain unvalidated.
- Confidence validation rejects booleans, non-numeric values, NaN, infinity, and values outside 0–1. Claim creation/review input types are hardened.
- Claim detail/list API now exposes `evidence_quality`; the Knowledge dashboard shows completeness and warnings.
- The system explicitly reports that provenance/completeness checks do not prove an excerpt semantically supports a claim. Semantic entailment and contradiction review remain future work and must not be automated as fact without a verifiable method.
- GitHub Actions passed on the phase code/UI head: 127 tests on Python 3.11 and 127 on Python 3.12; compileall succeeded.


### Phase 3 — Memory retrieval and governance (in progress, 2026-11-02)

- Memory writes now validate title/body types and size, require object-shaped JSON metadata, reject NaN/infinity/non-JSON values, and cap metadata at 8 KiB. Search query and limit types are checked.
- Context retrieval now ranks lexical matches with title weighting, groups multiple sources for the same validated claim, returns matched terms and retrieval-method metadata, and exposes bounded diagnostics via `retrieve_detailed` while preserving the existing `retrieve` interface.
- Added an authenticated `/api/v1/context/preview` endpoint and a dashboard preview that explicitly uses lexical-only retrieval, avoiding embedding/provider calls and cost during inspection.
- Fixed the memory category selector to offer only the supported episodic, semantic and procedural values (the previous UI default `note` was invalid).
- Added context and memory boundary tests. The latest full CI run is queued behind an older GitHub Actions run that has not reported job steps; do not treat Phase 3 as validated until the latest branch-head run completes successfully.


### Continuidade verificada — 2026-11-02

- Corrigido o diagnóstico da recuperação lexical: termos encontrados somente no título agora aparecem em `matched_terms`, alinhando explicabilidade e pontuação.
- Contratos de agentes agora validam IDs, papéis, operações, contexto permitido, estados de resultado e limites inteiros de passos (1–10). Isso fortalece a delegação determinística; **não** transforma os papéis em agentes LLM independentes nem habilita colaboração autônoma.
- Registro de ferramentas agora rejeita nomes/descrições/esquemas inválidos, classes de risco desconhecidas e permissões menos restritivas que o risco declarado.
- GitHub Actions passou no commit `26c77c3d0e3b7140e9bde3c1569d3c42e5443f6b`: **138 testes** em Python 3.11 e **138 testes** em Python 3.12; compilação dos módulos Python também passou.
- Os trabalhos continuam na branch de desenvolvimento. `main` permanece intacta; nenhum deploy, serviço remoto, provedor pago ou cobrança foi ativado.


### Worker local — validação adicional (2026-11-02)

- A fila local agora aceita somente payloads JSON-serializáveis finitos, exige objeto na entrada e no resultado, limita payload/result por bytes UTF-8 e rejeita valores NaN/infinito.
- A listagem da fila exige limite inteiro explícito entre 1 e 500; identificadores de proprietário vazios são rejeitados.
- GitHub Actions passou no commit `9d1a7fd7ba7ef2edd9538b0f3f6cec3f79da16e5`: **140 testes** em Python 3.11 e **140 testes** em Python 3.12; compileall passou.
- Isto fortalece o worker local existente. Ainda não existe protocolo de worker remoto/cloud; leases e fila local não equivalem a sincronização distribuída.
