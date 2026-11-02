# Development Checkpoint

**Atualizado:** 2026-11-01
**Projeto:** N.E.X.U.S. — Neural Engine Expert Underground System  
**Branch principal:** `main`

## Estado atual comprovado

O repositório possui um núcleo local em Python/SQLite, executável pela CLI, com:
- memórias episódicas, semânticas e procedurais;
- fontes e afirmações com estados explícitos de revisão;
- fila de tarefas e log de auditoria;
- ingestão de TXT/Markdown, SHA-256, trechos e busca lexical;
- pesquisa de metadados bibliográficos pela Crossref;
- política de ferramentas fail-closed;
- runtime textual com MockProvider offline.

**Não existe ainda:** provider remoto real, API HTTP, autenticação, interface web, ferramentas reais, memória integrada automaticamente ao contexto da conversa, worker cloud/PC, sincronização ou deploy.

## Endurecimento recente

- SQLite `:memory:` agora permanece disponível entre conexões curtas por meio de URI compartilhada e conexão âncora.
- Runtime reivindica cada tarefa por atualização condicional dentro de transação de escrita.
- Mensagens de exceção do provider não são armazenadas literalmente.
- Limites do runtime e identificadores de provider/model são validados.
- Testes novos cobrem persistência in-memory, reentrada de tarefa e não persistência de strings com aparência de segredo.
- Workflow observa o próprio caminho, usa permissões mínimas, executa compileall e unittest.

**CI:** execução [41255344883](https://github.com/VNSANTS/N.E.X.U.S/actions/runs/41255344883) concluída com sucesso em Python 3.11 e 3.12, incluindo compileall e unittest, no commit `59356b7674ee97b9c2357871d2221e35f7e53b59`.

**Estado registrado em 2026-10-31:** a execução local ainda estava pendente nessa data. Consulte a seção "Execução local — 2026-11-01" abaixo para o resultado posterior.

## Direção confirmada

- Assistente cloud-first acessível pelo navegador/celular.
- PC como worker opcional para ingestão e processamento pesado; núcleo básico não depende dele ligado.
- Meta de custo obrigatório zero no MVP, respeitando cotas reais dos serviços gratuitos.
- Processamento local leve devido ao i5 de primeira geração, 8 GB RAM e HDD.
- Aprovação específica para ações sensíveis.
- OpenJarvis permanece em checkout separado; reaproveitamento somente seletivo após validação local.

## Próximo passo técnico

1. Escolher o primeiro provedor remoto e validar protocolo, privacidade, cotas e custo.
2. Implementar um adaptador atrás de `ModelProvider`, mantendo MockProvider como padrão offline.
3. Definir autenticação e hospedagem antes da API pública.
4. Implementar API autenticada com isolamento de sessão.
5. Integrar memória ao contexto com consentimento, limite e proveniência.
6. Só então desenvolver worker, sincronização e UI.

## Documentação de referência

- `README.md`: visão, comandos e limites do protótipo.
- `PROJECT_STATUS.md`: histórico e situação detalhada.
- `ROADMAP.md`: fases de produto.
- `ARCHITECTURE.md`: arquitetura cloud + PC.
- `docs/MVP_SPEC.md`: escopo e critérios de aceite do MVP.
- `docs/IMPLEMENTATION_BACKLOG.md`: backlog técnico executável.
- `CODEX_HANDOFF.md`: handoff para Codex CLI.
- `DECISIONS.md`: decisões e questões pendentes.

## Execução local — 2026-11-01

- **Checkout:** `main`, commit-base `964a62bfca1ce42a75ed218143e2312c6100d420`, remoto configurado para `VNSANTS/N.E.X.U.S`. A referência local `origin/main` aponta para o mesmo commit; fetch não executado porque `debug.log` já estava não rastreado antes do trabalho.
- **Estado pré-existente preservado:** `debug.log` não foi lido, alterado nem removido; a nova regra `*.log` o ignora.
- **Alterações desta sessão:** endurecimento de `PolicyEngine` e teste de regressão em `nexus_learning/policy.py` e `tests/test_runtime.py`; exclusões de logs/backups/temporários em `.gitignore`; resumo do estado corrigido em `README.md`; registro de continuidade em `PROJECT_STATUS.md`, `CHECKPOINT.md`, `CHANGELOG.md` e `docs/IMPLEMENTATION_BACKLOG.md`.
- **Validação local:** `python -m compileall -q nexus_learning tests` passou; `python -m unittest discover -s tests -v` passou com 28 testes; CLI offline, ingestão/busca lexical e persistência SQLite temporária passaram. O teste foi executado em Python 3.13.17; CI ainda não executou estas alterações.
- **Codex multiagente:** seis perfis e configuração de projeto validados estruturalmente. A raiz Git não aparece explicitamente na lista local de projetos confiáveis; não foi alterada a configuração global, portanto o carregamento efetivo permanece a confirmar ao reabrir o Codex com o projeto confiável.
- **Próxima tarefa:** escolher e avaliar o provedor inicial (preço/cotas, privacidade, protocolo e uso em português) antes de implementar adaptador remoto. API e worker seguem bloqueados por provedor, autenticação, hospedagem e retenção.
- **Comandos executados:** `git status --short --branch`; `git branch --show-current`; `git rev-parse HEAD`; `git remote -v`; `git rev-parse origin/main`; `git diff --check`; `python -m compileall -q nexus_learning tests`; `python -m unittest tests.test_runtime.PolicyTests.test_truthy_non_boolean_values_never_grant_permissions -v`; `python -m unittest discover -s tests -v`; `python -m nexus_learning --help`; `python -m nexus_learning --db <SQLite temporário> runtime-once "Teste offline do N.E.X.U.S."`; `python -m nexus_learning --db <SQLite temporário> ingest-file <Markdown temporário>`; `python -m nexus_learning --db <SQLite temporário> document-search "lexical persistence"`; `python -m nexus_learning --db <SQLite temporário> stats`.

## Regras de continuidade

- Conferir branch e alterações locais antes de editar.
- Ler `AGENTS.md` e o backlog antes de qualquer implementação.
- Não substituir o núcleo nem reimplementar funcionalidades existentes.
- Não marcar uma capacidade como pronta apenas porque há documentação.
- Não adicionar chaves ou dados privados ao Git.
- Não habilitar shell, ferramentas sensíveis, deploy ou ações externas sem aprovação.
- Toda alteração deve ter teste; toda alegação de teste precisa de evidência.

## Continuidade — avaliação de provider e runtime (2026-11-01)

- Provider-neutral errors estão implementados em `nexus_learning/providers/errors.py`; runtime grava somente códigos/metadados seguros. Nenhuma escolha de provider ou adapter remoto foi feita.
- Comparativo oficial Gemini/Groq/OpenRouter: `docs/PROVIDER_EVALUATION_2026-11-01.md`.
- Auditoria de memória, runtime, seis perfis Codex e sequência de infraestrutura: `docs/RUNTIME_MEMORY_AND_MULTIAGENT_AUDIT.md`.
- Validação final: `python -m compileall -q nexus_learning tests` passou; `python -m unittest discover -s tests -v` passou com 31 testes; os seis TOMLs foram validados com `tomllib` (campos obrigatórios e nomes únicos); `git diff --check` passou.
- Integridade preservada: branch `main`, base `964a62bfca1ce42a75ed218143e2312c6100d420`; sem commit/push. As alterações locais anteriores foram mantidas. Não ler/modificar `debug.log`; não tocar no checkout separado OpenJarvis.
- Para retomar: `cd "<repo-root>"`; `git status --short --branch`; `python -m compileall -q nexus_learning tests`; `python -m unittest discover -s tests -v`. Próxima decisão do proprietário: provider/model, benchmark pt-BR, retenção/privacidade e origem de credencial/custo máximo.

## Continuidade — aplicação local integrada (2026-11-01)

- API WSGI e interface web estão em `nexus_learning/api.py` e `nexus_learning/web/index.html`; guia completo: `docs/LOCAL_API.md`.
- `python -m nexus_learning --db nexus_learning.db serve` cria o primeiro usuário com prompt local e serve somente em `127.0.0.1:8765`; `python -m nexus_learning --db nexus_learning.db worker --poll 1` executa a fila segura separadamente.
- Autenticação, sessões, mensagens, tarefas, recuperação contextual, claims/fontes, ferramentas READ, agentes determinísticos, atividade e fila local estão implementados. Persistência em SQLite existente é por tabelas aditivas.
- Adapters Gemini/Groq/OpenRouter são opcionais, padrão permanece MockProvider. Para evitar uso acidental de variáveis/credenciais preexistentes, remote requer `NEXUS_ENABLE_REMOTE_PROVIDER=true` além de seleção explícita. Nenhuma requisição remota foi feita.
- Validação final da implementação integrada: `python -m compileall -q nexus_learning tests` passou; suíte completa passou com 47 testes após enforcement single-owner; `python -m nexus_learning --help`, `serve --help`, `worker --help` e `git diff --check` passaram. Teste HTTP usou somente `127.0.0.1` com banco em memória; adapters usaram openers simulados.
- Limites: API local sem TLS, chat síncrono, sem cancelamento de request ativa, sem multiusuário de produção, sem worker cloud e sem colaboração autônoma geral entre modelos. Não expor à rede.
- Nenhum commit/push; preservar todas as alterações anteriores e não acessar `debug.log` ou o checkout OpenJarvis.
- Jobs de worker agora são associados ao usuário autenticado nas rotas API; leases usam fencing token e `fail()` serializado para impedir que worker antigo altere lease novo. Repostas malformadas do provider viram erros padronizados.

## Continuidade - ciclo inteligente e integracoes (2026-11-01)

- Ciclo persistente de dez fases, fila idempotente, recuperacao limitada, scheduler local, painel conectado, perguntas humanas, tarefas de aprofundamento e papeis internos. Consulte `docs/CONTINUOUS_LEARNING.md`.
- Integracoes: Gemini geracao/analise e embeddings; Tavily search/extract; Crossref publico; GitHub read-only. Consulte `docs/INTEGRATIONS.md`.
- `.env` ausente; chaves Gemini/Tavily/GitHub nao estao no processo. Nenhuma chamada real foi feita. MockProvider e padrao; budget remoto inicia desativado.
- Validacao final: `python -m unittest discover -s tests -v` passou com 72 testes; `python -m compileall -q nexus_learning tests` e `git diff --check` passaram.
- O script de inicializacao automatica foi somente criado e analisado; nenhuma tarefa do Windows foi registrada.
- Proximo: quando o proprietario configurar `.env`, configurar budget baixo no painel e executar checagens de conexao explicitamente.


## Continuidade ? motor de conversa local (2026-11-01)

- Configura??o real: `.env` local aponta para `http://127.0.0.1:11434`, `qwen2.5:0.5b`; banco `nexus_learning.db` persiste `ollama/qwen2.5:0.5b`. Nenhum segredo est? configurado para providers remotos.
- Conversa autenticada via `POST /api/v1/sessions/{id}/messages/stream` foi executada contra Ollama real; resposta e metadados apareceram no hist?rico. Qualidade limitada: uma pergunta simples 2+2 recebeu resposta ?3?.
- Testes completos chegaram a 83 testes e revelaram duas falhas; ambas foram corrigidas e os sete testes direcionados passaram. Rodar novamente `python -m compileall -q nexus_learning tests` e `python -m unittest discover -s tests -v` para obter o resultado completo p?s-corre??o.
- Ler `docs/LOCAL_API.md` e `docs/INTEGRATIONS.md` para configura??o, sele??o de modelos, comportamento de streaming e limita??es de qualidade.
- Nenhum commit/push. Preservar todas as altera??es preexistentes. N?o ler/alterar `debug.log`; n?o tocar checkout OpenJarvis.


## Continuidade ? Gemini/Tavily ligados (2026-11-01)

- `.env` local contem as chaves fornecidas, ACL restrita ao usuario atual e permanece ignorado pelo Git. Nao copiar valores para outros arquivos, logs ou relatorios. Recomendar rotacao das chaves por terem sido enviadas na conversa.
- `NEXUS_REMOTE_PROVIDERS=gemini` habilita somente Gemini entre os providers remotos; `NEXUS_PROVIDER` e selecao persistida continuam Ollama/Qwen. `NEXUS_TAVILY_ENABLED=true`; autonomia de pesquisa e aprovacao de custo recorrente permanecem false.
- Verificacao real de conexao via API local autenticada: Gemini connected, 46 modelos, `gemini-2.5-flash` disponivel; Tavily connected via `/usage`, uso de creditos inalterado em zero. Nenhuma geracao Gemini ou busca Tavily foi feita.
- Budget de inferencia LLM continua desligado. Para conversas Gemini, selecionar modelo e habilitar um limite deliberado na UI; para Tavily, pesquisa manual na tela Integracoes exige confirmacao.
- Testes novos verificam Gemini list-models sem geracao, Tavily GET `/usage` sem busca, allowlist remota e check API sem tokens/creditos. Validacao final: `python -m compileall -q nexus_learning tests`, `python -m unittest discover -s tests -v` (88 testes) e `git diff --check` passaram.

## Continuity - ALL FOR ONE / initial routing (2026-11-01)

- Audit confirmed that chat provider selection remains manually persisted; automatic model routing is not yet connected to chat runtime.
- Added `nexus_learning/model_router.py`: pure deterministic policy for SIMPLE, STANDARD, ADVANCED and RESEARCH; filters availability, capability, context, cost and latency metadata; fallback stays within local/remote trust boundary.
- Fail-closed behavior: remote candidates require explicit remote permission and budget authorization; unavailable, disallowed, malformed or insufficient-context candidates are rejected.
- This policy is not yet wired into runtime provider choice. Model latency, price and capability metadata need a trusted catalog or reviewed configuration before automatic routing. Manual Ollama/Qwen selection remains unchanged.
- Product-agent roles remain sequential and deterministic, not independent LLM agents. Research, knowledge and memory infrastructure exist, but chat does not delegate model tool calls. No Gemini generation or Tavily search was run during this work.
- Initial integrity audit found numerous existing local changes; all preserved. `.env` and local database remain Git-ignored. No commit/push. Codex profiles passed static validation, but subagent startup failed because the local OAuth token had been invalidated after the user's logout; no global settings were changed.
- Verification: `python -m compileall -q nexus_learning tests` passed; `python -m unittest discover -s tests -v` passed with 97 tests, including 9 router tests; `git diff --check` passed.

## Resume point: integrated routing and confirmed research (2026-11-01)

Working tree preserved. The chat endpoints now resolve the provider via `ModelRoutingService`; manual is default and automatic mode is configured through `NEXUS_ROUTING_MODE` plus `NEXUS_ROUTER_CANDIDATES`. Remote inference still requires explicit provider allowlisting and an enabled bounded budget. Candidate metadata must state context and capabilities and is checked against live availability.

Chat requests classified as research require a per-request `confirm_research: true` before Tavily is called. The unconfirmed path does not create conversation messages or usage reservations. Confirmed results become persisted untrusted sources, are supplied as system data with `[S1]` citation instructions, are returned as `sources`, and appear in `GET /api/v1/sessions/{id}/research`. The UI asks before retrying the streaming request and displays safe external links.

The tool registry has a policy-gated sensitive `research.search` entry. The post-generation reviewer checks source citations. Memory retrieval remains integrated; no generated answer becomes a confirmed fact or memory automatically.

Verification from this checkpoint: `python -m unittest discover -s tests -v` passed (114 tests); `python -m compileall -q nexus_learning tests` passed. No remote generation/search was run.

Next: verify UI behavior in a local browser; implement provider-native tool calls and continuation only with capability-specific contracts; make independent agent work budgeted and auditable; implement isolated improvement proposals with tests; add explicit research-intent/confirmation coverage to browser E2E. Do not claim those pending parts are done.


## 2026-11-01 - Gemini/OpenAI adapter validation

- provider_from_env now enforces an explicit NEXUS_REMOTE_PROVIDERS allowlist, aligned with ProviderManager. An empty value denies every remote provider; an absent variable preserves legacy global-opt-in behavior.
- Mock tests cover Gemini/OpenAI SSE, manual selection and redacted status, plus automatic OpenAI routing with test-only budget authorization.
- No local credentials were read, no live provider request was issued, and no credits were consumed. No budget setting or runtime default was changed.
- Verification: python -m compileall -q nexus_learning tests passed; python -m unittest discover -s tests -q passed (119 tests); git diff --check passed with only the existing README.md LF-to-CRLF warning.


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


### Segurança da sessão no navegador — 2026-11-02

- O token de autenticação deixou de ser gravado em `sessionStorage`; permanece somente em memória JavaScript durante a sessão da página. Atualizar/reabrir a página exige novo login.
- A rota de streaming agora trata HTTP 401 limpando o token em memória e retornando a interface ao login, alinhada ao helper da API.
- Adicionados testes estáticos para impedir regressão de persistência do token e verificar o fluxo de expiração.
- GitHub Actions passou no commit `3916ddc36d786108fb109ac91f4370c37c5d435a`: **142 testes** em Python 3.11 e **142 testes** em Python 3.12; compileall passou.
