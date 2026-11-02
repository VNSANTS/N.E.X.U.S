# Development Checkpoint

## Continuidade remota — CI e auditoria de evidências (2026-11-02)

- Branch de trabalho: `nexus/remote-continuation`; PR #3 continua aberto e direcionado a `nexus/review-nov-02`, não à `main`.
- Commit `d11adc710e149dd17b94294de76b89d798c8c571`: GitHub Actions passou com 187 testes unitários em Python 3.11 e 3.12; browser E2E Playwright/Chromium também passou. Este resultado é anterior às novas alterações de evidência.
- P1-04: `NEXUS_AGENT_MODELS` permite configurar provider:model por Architect, Analyst e Reviewer. ProviderManager mantém opt-ins/allowlists/credenciais; o preflight inclui apenas chamadas remotas e cada chamada remota exige sua reserva individual. Sem descoberta automática de capacidade/disponibilidade ou fallback same-lane.
- P1-05: busca autenticada de Skills agora usa `QUERY_STRING`; o bug de `UnboundLocalError` causado por imports locais de `parse_qs` foi corrigido e o CI passou.
- P1-06 em implementação: o pipeline recebe até três fontes, atribui IDs S1–S3 e valida determinísticamente que cada claim referencie apenas IDs fornecidos. Claims sem referência ficam `unreferenced`; IDs fabricados/duplicados são rejeitados. Isso comprova apenas ligação a uma fonte fornecida, não a verdade/confiabilidade da fonte. A nova etapa ainda aguarda CI.
- Próxima validação: suíte CI completa, incluindo browser E2E, para as alterações de evidence claims e preflight.


## Último snapshot publicado — 2026-11-02

- Branch remota de referência: `nexus/review-nov-02`; commit `16991c3aaf030f2ff9ef9233b61253c100a82538`. A branch não foi mesclada em `main`.
- Codex reportou 183 testes unitários aprovados, 5 E2E opcionais ignorados, `compileall` e `git diff --check` aprovados antes da publicação. CI remoto não havia sido executado.
- Gemini e Anthropic já tinham tool calling nativo com preservação do turno original; Skills aprovadas eram carregadas sob demanda no chat síncrono/SSE.
- Pendências comprovadas nesse commit: seleção de modelos independentes por especialista, auditoria estruturada de evidências, delegação mais forte, eventos na UI, CI remoto, sandbox real e implantação cloud.
- O trabalho remoto subsequente está em `nexus/remote-continuation`; não o considere validado até CI/testes passarem. Ele adiciona mapa de provider/model por especialista com budget preflight, correção do query string de Skills e testes de regressão.
- Os registros abaixo são checkpoints históricos e não devem ser usados isoladamente como estado atual.

## Continuidade - pipeline de especialistas (2026-11-02)

- O checkout continua na branch `main`, HEAD `852131e52f454175c501e6f36bcea2c04a73e9e7`, sem commit/push nesta rodada. Alteracoes locais anteriores foram preservadas.
- A pipeline opt-in `nexus_learning/agent_execution.py` foi conectada aos fluxos POST de conversa normal e streaming. ADVANCED/RESEARCH podem executar Architect → Analyst → Reviewer no provider/model selecionado e passar deliverables delimitados como dados não confiáveis ao modelo final.
- A opção `NEXUS_MULTIAGENT_ENABLED=false` foi adicionada a `.env.example`. Só habilitar explicitamente; adiciona três chamadas antes da geração. Pesquisa Tavily mantém sua confirmação própria.
- Para providers remotos, o sistema verifica orçamento para o lote antes da primeira chamada, e cada inferência continua exigindo reserva atômica individual. O preflight não reserva o lote atomicamente: concorrência ou redução do orçamento pode deixar uma execução parcial, mas o limite monetário configurado segue protegido.
- O histórico de atividade registra início/conclusão/falha e dimensões das chamadas; não armazena prompts nem entregáveis. Cada papel continua sem ferramentas e usa o mesmo modelo. A arquitetura não representa agentes com seleção independente de modelo.
- Testes novos cobrem fluxo normal, streaming, chamadas remotas com orçamento, bloqueio remoto sem orçamento, falha de especialista sem chamar a resposta final, segurança dos eventos e saída estruturada.
- Verificação final local: `python -m compileall -q nexus_learning tests` passou; `python -m unittest discover -s tests -q` passou com 162 testes (5 ignorados por serem E2E opt-in); Playwright/Chromium `python -m unittest discover -s tests/e2e -v` passou com 5/5, incluindo a conversa especialista opt-in. Nenhuma chamada externa foi feita.
- CI não foi executado remotamente (não houve push); YAML parser local não está instalado. A configuração do workflow foi inspecionada, mas apenas as execuções locais são evidência disponível.
- Nenhum provider externo, serviço pago ou Tavily foi chamado. Configuração multiagente permanece desativada por padrão.

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


## Continuidade - revisao de integridade e orcamento (2026-11-02)

- Checkout preservado em `main`, commit `852131e52f454175c501e6f36bcea2c04a73e9e7`; apos `git fetch origin main`, `origin/main` estava no mesmo commit. Sem merge, commit ou push.
- Revisao leu documentacao e arquitetura; `.env` foi consultado apenas para switches/endpoint nao secretos, sem exibir credenciais; banco local e `debug.log` nao foram lidos. Nenhuma chamada a Gemini, OpenAI, Tavily ou outro servico externo.
- Corrigida a concorrencia da idempotencia no enqueue via `BEGIN IMMEDIATE` e lock local; teste com banco SQLite em arquivo cobre chamadas simultaneas com o mesmo identificador.
- Estimativa de entrada para orcamento usa bytes UTF-8 e margem de enquadramento. Corrigido risco P1: `_reserve` le autorizacao e limites depois de obter `BEGIN IMMEDIATE`, na mesma transacao da reserva.
- Teste de regressao reproduziu a autorizacao obsoleta antes da correcao; testes focados de worker, orcamento e roteamento passaram. `python -m compileall -q nexus_learning tests` e `python -m unittest discover -s tests -q` passaram, com 122 testes.
- Limite: estimativa local de tokens/custo nao equivale ao tokenizer ou faturamento real do provedor. Nao habilitar chamadas pagas com base somente nessa estimativa.
- Browser E2E: `tests/e2e/test_browser_ui.py` uses an in-memory SQLite DB, injected deterministic provider, ephemeral loopback server, and headless Chromium. Four browser tests passed; Playwright 1.64.1 and Chromium were installed only in a temporary environment/cache, not as runtime or CI dependencies.
- Recovery tests cover expired lease after engine/worker reconstruction, committed checkpoint without next enqueue, duplicate owner question prevention, uncertain research reservation without retry, completed and partial-failure result recovery, additive schema migration, failure-label allowlisting, and atomic rollback/retry for task-link creation.
- Multiprocess worker tests cover one claimant per job, idempotent enqueue across independent processes, and stale-token rejection. Long-running handlers renew leases and worker heartbeats; terminal lease expiry records `lease_expired` plus a failure event.
- `.github/workflows/learning-core-tests.yml` now has a separate Playwright/Chromium E2E job. The workflow was validated by local test runs only; no GitHub Actions run is available without a push or PR.
- Chromium exposed a UI defect: the Learning page passed the wrong value into `listRows`, causing `(rows || []).slice is not a function`; fixed and covered by E2E navigation.
- Owner answer resume now increments the idempotency generation and stores the answer in the cycle checkpoint. Consent and memory/audit persistence share a transaction when the owner requests remembering.
- Research reservation is unique per cycle and written before outbound I/O. Recovery reports the persisted result, including sanitized provider failures, or an uncertain status when interruption occurred before completion; it never retries the reserved request. Exactly-once provider delivery is not guaranteed.
- Context recovery applies a global item cap and prioritizes validated claims with provenance when semantic results would otherwise fill the cap.
- Final validation: `python -m compileall -q nexus_learning tests` and `python -m unittest discover -s tests -q` passed with 144 tests (4 optional E2E tests skipped by default); `python -m unittest discover -s tests/e2e -v` passed all 4 Chromium browser tests. `git diff --check` passed.
- No remote provider or research calls were made. Next: expand multi-process worker races and external-request in-flight tests; consider CI E2E without making browser a runtime requirement.
## Tool calling — implementação local, 2026-11-02

ModelResponse agora aceita chamadas tipadas opcionais. O ciclo usa ferramentas READ, limita rodadas, chamadas, tempo e tamanho de payload e mantém os resultados como dados não confiáveis. Ollama e OpenAI-compatible são implementados; o uso exige allowlist local explícita por provider:model. Gemini/Anthropic ficam sem tool calling até adapters nativos serem implementados. Pesquisa Tavily permanece no fluxo de confirmação do proprietário.

- Endpoint POST síncrono: tool calling disponível para modelo explicitamente permitido.
- SSE: streaming e cancelamento preservados; schemas de ferramenta não são anunciados, pois o transporte de geração síncrona não permite cancelamento confiável.
- Especialistas: pipeline opt-in Architect → Analyst → Reviewer permanece sequencial/tool-less; demais papéis são supervisionados deterministicamente. Não é uma rede paralela de agentes independentes.
- Skills do produto e execução isolada de código ainda não implementadas.
- Cópia do comparative review foi lida na branch fonte do PR #2, pois o arquivo não existe localmente; nenhuma alteração Git remota foi feita.

Continuar com: testar a suíte completa depois desta rodada; então implementar streaming com cancelamento real ou preparar o fluxo de confirmação para ferramenta sensível sem contornar o consentimento existente. Não habilitar Tavily ou providers remotos automaticamente.


## Registro de execução — 2026-11-02T15:33:40+00:00

- Tarefa: `P1-05` — **CONCLUÍDA E TESTADA**
- Resumo: AGENTS.md agora exige retomar plano/checkpoint; NEXUS_EXECUTION_PLAN.md ordena backlog e tools/update_checkpoint.py registra marcos sem apagar histórico. Skills aprovadas são selecionadas e injetadas no chat como instruções não confiáveis; teste de API autenticada comprova que skill proposta não é carregada e aprovada é.
- Testes (resultado observado): API skill integration: passou; tests/test_skills.py 3 passaram; compileall passou.
- Arquivos: AGENTS.md, NEXUS_EXECUTION_PLAN.md, tools/update_checkpoint.py, nexus_learning/api.py, tests/test_api.py, CHECKPOINT.md
- Próxima tarefa: P1-04 modelos independentes por especialista; P1-06 auditoria de evidências


## Evidence handoff policy — 2026-11-02

- Previous green CI head: `373a55e803269ad9489d6ea4b26ce228e7738965`; 190 unit tests passed in Python 3.11 and 3.12; browser E2E: 5/5 passed.
- New pending change: synthesis serialization deterministically withholds `unreferenced` specialist claims whenever a source catalogue is present, preserving a per-agent withheld count. The final synthesis prompt states that `source_linked` is a traceable reference, not a proof, and that summaries/items remain untrusted analysis.
- Reviewer receives explicit instructions to call out factual claims without supplied source IDs. The filtering is structural; semantic support and truth still require review.
- New unit coverage: linked claims retained, unreferenced claims withheld, no-source claims remain visibly unreferenced, invalid result types rejected. CI pending for this delta.


## P1-06 — withholding policy validated (2026-11-02)

- Latest CI head: `18347368767042b78cfa86e0617550928a8152c0`.
- GitHub Actions passed: 193 unit tests in Python 3.11, 193 in Python 3.12, and 5/5 Playwright/Chromium browser E2E tests. Compile step passed in both Python versions.
- With a source catalogue present, final synthesis now deterministically receives only `source_linked` specialist claims; unreferenced claims are withheld and counted per agent. The Reviewer is prompted to flag factual statements without a supplied source ID. Summary/item fields remain untrusted analysis.
- Without sources, claims remain labelled `unreferenced` and are explicitly described to final synthesis as analysis, not verified facts.
- This is structural reference hygiene, not semantic validation. It does not prove the source is reliable or that the claim is true.
- Next: P2-01 bounded delegation with explicit stage records, resumability/cancellation semantics and no cycles. Do not introduce parallel execution until isolation and budget accounting are sound.


## P2-01 bounded-stage deadline — 2026-11-02 (CI pending)

- Added a global specialist pipeline deadline (90 seconds default, constructor maximum 180 seconds). Each provider call receives the remaining time capped by the existing per-call timeout.
- If a stage returns after the global deadline, it is reported as `pipeline_timeout`; remaining specialists are marked skipped and final synthesis is not called.
- Tests cover an overlong first stage and reject invalid/unbounded deadline settings.
- Timeout is cooperative through provider/HTTP timeout; no false claim of forcibly stopping a non-cooperative external provider.


## P2-01 — deadline and stage-stop validation (2026-11-02)

- Commit `029389e9a7ff3781ca0ec00770e2f7eaf1585927` passed full GitHub Actions: Python 3.11: 195 unit tests; Python 3.12: 195 unit tests; Playwright/Chromium: 5/5.
- Specialist stages now share a 90-second global deadline by default (maximum configurable constructor bound 180s). Each call receives remaining time no greater than the per-call timeout.
- Overrun becomes `pipeline_timeout`; later stages are skipped and the final synthesis is not called. This relies on the provider respecting its timeout parameter.
- Still pending: durable stage checkpoint/resume, same-trust-lane fallback after safe pre-call failure, parallel work only after isolation/budget correctness.
- Next task: P2-02 independent review and provenance.


## P1-05 — skills discovery and integrity hardening (2026-11-02, CI pending)

- Replaced SQL `LIKE` discovery with literal case-insensitive filtering over approved skill metadata, so '%' and '_' in user queries cannot turn the search into a wildcard match.
- Discovery limit must be an integer 1–50; selection limit must keep max_skills within 0–10 and max_chars within 0–12000. Booleans and invalid bounds are rejected.
- Added regression tests for wildcard search, invalid limits and SHA-256 integrity drift after approval.
- Skills remain text-only, untrusted suggestions; this does not grant tools or execution privileges. CI pending.


## P1-05 — Skills discovery and integrity hardening validated (2026-11-02)

- CI head: `182f59ea06897a9e4eaafff1e1866597b51fe2aa`.
- Python 3.11: 199 tests passed (5 opt-in E2E skipped by standard discovery).
- Python 3.12: 199 tests passed (5 opt-in E2E skipped by standard discovery).
- Browser E2E: 5/5 passed.
- Skill search treats wildcard symbols as literal text; query/selection limits reject invalid values; tampered approved instructions fail the stored SHA-256 integrity check.
- Remaining: skill-management UI and semantic instruction-conflict detection; no execution/permission capabilities are granted.
- Next: P2-02 independent review/provenance.


## P2-02 — typed Reviewer assessments (2026-11-02, CI pending)

- Reviewer schema adds a one-to-one `reviews` array for Analyst claims: zero-based `claim_index`, assessment `supported` / `unsupported` / `uncertain` / `conflicting`, note up to 100 chars.
- The parser rejects incomplete/duplicate review coverage, invalid indices/assessment/note, and any `supported` assessment where the Analyst claim has no supplied evidence ID. Reviewer cannot add claims.
- Synthesis drops Analyst claims assessed `unsupported` or `conflicting` even if source-link filtering is disabled; uncertain claims remain labelled. The final response is instructed not to restate rejected claims as facts.
- Activity events include `separate_review_model` to distinguish a reviewer configured with a different provider/model. That is model diversity, not proof or human approval.
- New unit tests cover exact review coverage, unsupported source-less claims, suppression and model difference. An API integration fixture exercises an unsupported Analyst claim through the real conversation route.
- CI pending for this delta.


## Reviewer preflight footprint adjustment — 2026-11-02 (CI pending)

- Reduced specialist output bounds to summary 160 chars, at most two items (100 chars each), one claim (50 chars) and Reviewer note (60 chars). Source references still cap at three IDs.
- Worst-case preflight placeholders were aligned to the accepted schema, retaining the default 12,000-character specialist input limit and 24,000-character API pipeline limit.
- Updated synthesis test to assert the structured review assessment/note metadata.
- CI pending.


## P2-02 — typed Reviewer assessments validated (2026-11-02)

- CI head: `0ff391c0fd4642d6d1792c310b91d9a01ece1db5`.
- Python 3.11: 203 tests passed; 5 optional E2E skipped by standard discovery.
- Python 3.12: 203 tests passed; 5 optional E2E skipped by standard discovery.
- Playwright/Chromium browser E2E: 5/5 passed.
- Reviewer produces one bounded typed finding per Analyst claim; the parser enforces complete one-to-one index coverage and rejects fabricated/missing findings.
- Unsupported/conflicting claims are removed before final synthesis; uncertain claims remain visibly labelled. Supported is rejected if no evidence ID was supplied.
- The API preflight placeholder now uses fixed claim index zero; the integration test confirms that a Reviewer-rejected statement is not included in final synthesis.
- This is structural review metadata and an LLM opinion, not independent verification or human approval.
- Next: re-evaluate the sandbox blocker and continue any secure, non-destructive work. No cloud deployment or privileged execution is authorized.


## P2-04 — specialist activity UI (2026-11-02, CI pending)

- Added a dedicated authenticated metadata-only endpoint `GET /api/v1/agents/activity`; it returns only specialist LLM events belonging to the signed-in user and filters the detail payload on the server.
- The Agentes page displays the role roster and up to 40 recent LLM stage events, with provider/model, stage, time, duration, character counts and safe failure metadata.
- API test exercises unauthorized access, another user's event isolation, and redaction of injected prompt/response/tool-result fields.
- Browser rendering uses node/textContent helpers; no dynamic HTML strings or arbitrary activity JSON are inserted.
- CI pending.


## Skills administration + sanitized agent activity — 2026-11-02

- Latest code head validated by CI: `ed844c370458a8b8a8f233965b9043f23286af36`.
- GitHub Actions passed: Python 3.11 — 211 tests; Python 3.12 — 211 tests; Playwright/Chromium browser E2E — 7/7. Compile step passed in both Python jobs.
- Skills registry now supports owner-reviewable pending proposals, explicit approval and explicit rejection, with audit records. The UI lets the owner propose a text-only skill, inspect the full instruction body, approve/reject after confirmation, and search approved skills.
- The API proposal-list route is authenticated. Rejected skills are removed from the pending queue and never appear in approved discovery.
- Agent activity is read via `GET /api/v1/agents/activity`, which returns only allowlisted metadata for `agent.llm_*` events belonging to the authenticated owner. Prompts, model responses and tool results are filtered server-side.
- The Agentes UI renders roster and specialist LLM activity metadata. The UI uses DOM text nodes, not HTML insertion.
- PR #3 remains open, based on `nexus/review-nov-02`; no merge into `main`.
- Next priority: durable specialist-stage checkpoint/resume and carefully bounded same-trust-lane fallback; keep sandboxed code execution blocked until an actual isolation runtime is validated.


## Skills integrity at approval boundary (2026-11-02, CI pending)

- `SkillRegistry.approve` re-fetches the proposal under `BEGIN IMMEDIATE`, recomputes the SHA-256, and refuses approval when instructions differ from the original proposal.
- `GET /api/v1/skills/proposals` returns an `integrity_ok` flag. The UI displays it and disables approval when false.
- Added registry/API/Playwright tests for tampered proposals remaining pending and the approval button being disabled.
- CI pending.
