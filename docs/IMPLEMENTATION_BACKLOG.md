# N.E.X.U.S. — Backlog técnico de implementação

**Data da revisão:** 2026-11-02
**Escopo:** revisão somente do repositório N.E.X.U.S.; não inclui Nexus Finance nem outros projetos.

Este documento é o plano operacional derivado do código e da documentação existentes. Ele separa o que está no repositório do que ainda depende de escolhas, credenciais ou execução no computador.

## 1. Estado verificado no codigo - revisao 2026-11-02

| Area | Evidencia no repositorio | Estado real |
|---|---|---|
| Persistencia e memoria | `nexus_learning/engine.py`, `memory.py`, `knowledge.py` | SQLite local; memorias, fontes, afirmacoes, auditoria e recuperacao contextual lexical. Promocao exige revisao; saidas de modelo nao viram fatos automaticamente. |
| Ingestao e pesquisa | `ingestion.py`, `research.py`, `crossref.py`, `integrations/` | TXT/Markdown e busca lexical; Crossref publico; Tavily requer configuracao e confirmacao explicita. Nenhuma pesquisa real foi executada nesta revisao. |
| API e interface | `api.py`, `web/` | WSGI autenticada em loopback, sessoes/historico e interface conectada. Nao e implantacao remota/de producao; sem TLS de producao ou multiusuario. |
| Provedores e roteamento | `providers/`, `routing.py`, `model_router.py`, `provider_budget.py` | Adaptadores opcionais, selecao manual/automatica e preflight de capacidade. Chamadas remotas exigem permissoes e orcamento explicitos; MockProvider continua para offline/testes. Nenhuma chamada real nesta revisao. |
| Ferramentas e agentes | `tools.py`, `agents.py`, `agent_execution.py`, `runtime.py`, `api.py` | Ferramentas continuam allowlisted e policy-gated. Há pipeline LLM opt-in Architect→Analyst→Reviewer antes de respostas ADVANCED/RESEARCH, sem tools e com contexto explícito, saída JSON validada, orçamento fail-closed e eventos sem conteúdo bruto. Usa o mesmo provider/model e não armazena entregáveis; ainda é colaboração sequencial limitada. |
| Worker e tarefas | `worker.py`, `learning_cycles.py` | Fila SQLite local com prioridade, idempotencia, leases renovaveis, fencing e limites; concorrencia testada com processos independentes. Nao e worker distribuido. |
| Seguranca/orcamento | `auth.py`, `policy.py`, `provider_budget.py` | Auth local e autorizacao fail-closed; orcamento estimado com reserva transacional. Estimativa nao garante valor final cobrado pelo fornecedor. |
| Testes | `tests/`, `.github/workflows/` | `unittest` e mocks; 162 testes passaram localmente em Python 3.13.17 (5 E2E opt-in ignorados na descoberta padrão), e 5 testes Playwright passaram no Chromium, incluindo conversa com pipeline LLM mockado no browser. Workflow CI tem job browser separado, ainda sem execução remota. Integrações externas não foram chamadas nesta rodada. |

O historico abaixo registra marcos anteriores; nao trate anotacoes antigas como estado atual quando contradisserem esta tabela.

### Pipeline especialista opt-in - 2026-11-02

- `NEXUS_MULTIAGENT_ENABLED=false` por padrão. Quando habilitado, somente solicitações classificadas como ADVANCED ou RESEARCH executam Architect → Analyst → Reviewer e depois a resposta final.
- Os papéis usam o mesmo provider selecionado, são sequenciais, sem ferramentas e com contextos permitidos por papel. Saídas são JSON limitadas, tratadas como dados não confiáveis; prompts/saídas não são gravados na atividade.
- Pesquisa continua exigindo confirmação antes do pipeline. O worker/API não ganha autorização para ferramentas ou ações externas.
- Em providers remotos, a aplicação faz preflight de orçamento para as três etapas e a resposta final; cada chamada ainda passa pela reserva atômica existente. Uma mudança concorrente de orçamento pode interromper o pipeline depois de uma ou mais chamadas, sem ultrapassar os limites.
- Testes offline cobrem execução, streaming, registros, falha fail-closed sem orçamento remoto e contabilização de todas as chamadas. Não houve chamadas externas reais.

### Continuity implementation - 2026-11-02

- Worker/cycle tests reconstruct file-backed SQLite services across lost leases, committed checkpoints with lost follow-up enqueue, interrupted questions, uncertain external research, and task/link transaction interruption.
- Research reservation is unique per cycle and committed before external I/O. After overlap/restart, the cycle records an uncertain outcome rather than issuing a duplicate request. This is at-most-once after reservation, not exactly-once delivery.
- Owner answers resume with a new idempotency generation; the answer is copied into the cycle checkpoint. When `remember=true`, question state, checkpoint and memory/audit entry are committed together.
- Context retrieval caps the aggregate result count and puts validated sourced claims ahead of semantic/lexical memories when the cap is reached.
- Optional Playwright E2E passed locally using a temporary environment and browser; see `tests/e2e/test_browser_ui.py` and `requirements-e2e.txt`. No dependency was added to runtime requirements. CI now has a separate browser job; the workflow has not yet run remotely.
- The E2E failure that found the learning page's incorrect `listRows` arguments was corrected and all 4 browser tests passed.
- Completed research outcomes and sanitized provider failure metadata are now persisted before cycle checkpointing, so restart recovery preserves partial/failed/no-result status without retrying the external request. A migration test covers existing reservation tables; provider, operation, and error labels are allowlisted.
- Independent-process tests cover exclusive claims, same-key enqueue idempotency, and stale-worker fencing. `LocalWorker` renews leases while handlers run; exhausted expired leases now store a failure code and activity event.

## 2. Endurecimento aplicado nesta revisão

- Corrigido o modo SQLite `:memory:`: como o engine abre conexões curtas por operação, agora usa uma URI SQLite compartilhada com uma conexão âncora para manter o banco em memória vivo.
- Adicionado `LearningEngine.close()` para liberar a conexão âncora desse modo.
- O runtime agora reivindica uma tarefa com transação de escrita e atualização condicional. Uma tarefa que já está `running` não deve ser iniciada novamente por outra chamada.
- Mensagens de exceção do provider deixaram de ser persistidas literalmente. Elas podem conter URLs, cabeçalhos ou credenciais; o banco guarda um resumo seguro e o tipo da exceção.
- O runtime valida limites de entrada/saída e os campos essenciais do retorno do provider.
- Adicionados testes de regressão para banco em memória, reentrada da mesma tarefa, vazamento de mensagem sensível e limites inválidos.
- Corrigido o filtro de paths do workflow; agora ele observa o arquivo de workflow real. Adicionadas permissões mínimas, timeout e compilação antes da suíte de testes.

**Estado registrado na revisão de 2026-10-31:** as alterações daquela revisão foram gravadas no GitHub, e a execução local ainda não tinha sido feita. Esta atualização registra testes locais posteriores; CI desta mudança não foi executada.

### Verificação e hardening local — 2026-11-01

- Auditoria independente encontrou que argumentos truthy não booleanos (`approved="false"` ou `1`) podiam autorizar ações `SENSITIVE`, e `allow_reversible="false"` habilitava escrita reversível.
- Corrigido `PolicyEngine` para aceitar aprovação somente com `True` literal e rejeitar configuração reversível que não seja boolean.
- Teste de regressão adicionado em `tests/test_runtime.py`; reprodução pré-correção falhou e a regressão passou após a correção.
- Neste PC: `compileall` passou; os 28 testes `unittest` passaram em Python 3.13.17; CLI offline, ingestão/busca de Markdown e persistência SQLite temporária passaram.
- Esta validação é local; não representa CI. O adaptador remoto continua bloqueado pela escolha de provedor e requisitos de custo/privacidade.

## 3. Próximo marco recomendado — primeira conversa com IA real

Não implementar um provider por adivinhação. Antes, escolher o provedor e verificar seu protocolo, termos, limites, preço e política de dados.

### Tarefas

1. Definir a interface de configuração por ambiente, sem segredos no repositório.
2. Implementar um adaptador remoto atrás de `ModelProvider`.
3. Normalizar erros de autenticação, rate limit, timeout, indisponibilidade e resposta malformada.
4. Registrar provedor/modelo e uso de tokens somente quando reportado pela API.
5. Manter MockProvider como padrão de testes e modo sem internet.
6. Testar respostas vazias, falhas, limites e ausência de credencial.
7. Não adicionar fallback automático para outro fornecedor sem consentimento e regras de custo/privacidade.

### Critérios de aceite

- A aplicação continua funcionando sem chave e sem internet usando MockProvider.
- Segredos vêm do ambiente/secret store e nunca aparecem em logs, exceções persistidas ou Git.
- Timeout e rate limit resultam em falha controlada.
- O adaptador não executa ferramentas; devolve somente dados do modelo.
- Testes offline passam e um teste real é executado localmente pelo usuário com sua própria chave, sem compartilhá-la.

## 4. Próximo marco — API autenticada mínima

A especificação de endpoints está em `docs/MVP_SPEC.md`. Antes de codificar:
- confirmar framework e versão suportada pelo PC;
- escolher autenticação de usuário único;
- definir armazenamento de sessão e expiração;
- definir limites de requisição e tamanho do corpo;
- decidir onde ficará o backend e como guardar segredos.

Implementação inicial limitada:
- `POST /api/v1/tasks`;
- `GET /api/v1/tasks/{task_id}`;
- `GET /api/v1/sessions/{session_id}/messages`;
- `POST /api/v1/tasks/{task_id}/cancel`.

A API não pode confiar em `session_id` enviado pelo cliente sem verificar a titularidade. Toda consulta deve ser vinculada à identidade autenticada. Não expor SQLite, painel administrativo ou worker sem autenticação.

## 5. Próximo marco — memória na conversa

A memória já é persistida, mas ainda não é recuperada automaticamente pelo runtime de conversa.

Implementar somente depois de definir:
- quais memórias podem entrar no contexto;
- limite de caracteres/tokens por memória;
- regra de relevância;
- expiração e correção;
- consentimento para salvar fatos pessoais;
- como separar memória pessoal de conhecimento com fontes.

Critérios:
- contexto mínimo e limitado;
- memória arquivada nunca é recuperada;
- nenhuma memória é gravada automaticamente sem uma regra explícita;
- fontes e estado de validação acompanham conhecimento pesquisado;
- texto recuperado é dado, não instrução de sistema.

## 6. Próximo marco — worker do PC e nuvem

A arquitetura cloud + PC está documentada em `ARCHITECTURE.md` e D-014. O worker só deve começar depois que houver API autenticada e contrato de tarefas.

Requisitos mínimos:
- conexão de saída autenticada iniciada pelo worker;
- nunca abrir shell remoto ou porta pública de entrada;
- tipos de tarefa em allowlist;
- lease/expiração para evitar dois workers executarem a mesma tarefa;
- idempotência e retry limitado;
- heartbeat, cancelamento e estado `waiting_for_pc`;
- tamanho máximo de entrada/saída e limites de CPU/RAM;
- sincronização versionada, sem sobrescrever silenciosamente;
- fila local quando o PC estiver offline.

## 7. Decisões que continuam pendentes

| Decisão | Por que não foi escolhida automaticamente |
|---|---|
| Provedor de IA inicial | Afeta preço, quotas, privacidade, protocolo e disponibilidade em português |
| Hospedagem cloud | Plano gratuito pode ter suspensão, limites e armazenamento efêmero |
| Autenticação | Precisa proteger sessões e acesso remoto de um único usuário |
| Frontend | Reaproveitar UI existente (se houver em outro checkout) ou iniciar uma página web leve |
| Política de retenção | Define quanto tempo conversas, logs e memórias permanecem armazenados |
| Execução de testes no PC | Precisa confirmar ambiente, Python e consumo real no equipamento |

Nenhuma chave, cartão, domínio ou serviço pago deve ser presumido. A meta de custo obrigatório zero continua como objetivo, não como garantia de disponibilidade gratuita ilimitada.

## 8. Ordem recomendada para o Codex

1. Conferir a branch e o estado de trabalho local antes de editar.
2. Ler `AGENTS.md`, `CODEX_HANDOFF.md`, `PROJECT_STATUS.md` e este backlog.
3. Executar compileall e unittest; registrar resultados literais.
4. Corrigir regressões sem substituir o núcleo existente.
5. Implementar somente um adaptador de provider após o provedor ser escolhido.
6. Criar API/auth antes de qualquer worker remoto.
7. Integrar memória com testes de privacidade e isolamento.
8. Só então iniciar UI, worker e sincronização.

**Regra de conclusão:** nenhuma etapa é considerada concluída por existir documentação. Exigir código, teste executado e evidência de funcionamento.

## Atualização de continuidade — 2026-11-01

Concluído nesta sessão: comparação técnica baseada em documentação oficial (`docs/PROVIDER_EVALUATION_2026-11-01.md`), auditoria da memória/runtime/perfis (`docs/RUNTIME_MEMORY_AND_MULTIAGENT_AUDIT.md`) e taxonomia provider-neutral de falhas (`nexus_learning/providers/errors.py`) com persistência de diagnósticos seguros.

### Próximas tarefas em ordem

1. **Decisão humana:** escolher modelo/provider após benchmark pt-BR com conteúdo fictício; definir privacidade, retenção, custo máximo e fonte de segredo. Não codificar adapter real antes disso.
2. **Adapter:** implementar somente um adapter atrás de `ModelProvider`, configuração validada e testes simulados de sucesso, erros, timeout e resposta inválida. Sem fallback automático; projetar cancelamento real do transporte antes de prometer cancelabilidade.
3. **Sessões e API:** modelar sessão/mensagens, identidade única, isolamento, retenção e cancelamento; então construir API HTTPS autenticada.
4. **Ferramentas e supervisão:** registry allowlisted, permissões no runtime, aprovação explícita, budgets e auditoria antes de delegação multiagente de produto.
5. **Worker:** fila durável, lease, idempotência, retry limitado, heartbeat e conexão de saída, após API/auth.
6. **Interface e sync:** UI web pequena consumindo a API; sincronização versionada e minimizada após política de dados, backup/restore e conflitos definidos.
7. **Operação:** métricas e logs redigidos, limites/alertas, recuperação e testes de isolamento antes de execução autônoma.

No checkpoint de auditoria anterior à implementação da API, o runtime ainda não recuperava memória nem mantinha sessões. Essas duas capacidades agora têm integração lexical/contextual local; continuam pendentes semântica avançada, consentimento/retenção para cloud e sincronização. Saídas de modelo permanecem mensagens, nunca fatos automáticos. O carregamento real dos seis perfis Codex ainda precisa ser verificado após confiança explícita da raiz e reabertura da CLI; não alterar configuração global automaticamente.

### Estado após implementação local integrada — 2026-11-01

API local/auth, sessões e histórico, recuperação lexical limitada, tools READ, agentes determinísticos supervisionados, provider adapters opt-in e job queue persistente foram implementados. O runtime agora recebe histórico/contexto limitado; histórico de sessão e mensagens têm tabelas próprias. Memórias continuam sendo salvas explicitamente pelo usuário, e claims continuam exigindo revisão humana. Ver `docs/LOCAL_API.md`.

Próximas fatias após esta base: (a) executar e revisar manualmente a UI com dados fictícios; (b) decidir retenção, exportação/exclusão e política de identidade antes de qualquer remote exposure; (c) benchmark e decisão do provider; (d) adicionar cancelamento real com transporte suportado e chat assíncrono usando a queue; (e) adicionar testes de limites de concorrência e recuperação de processo; (f) selecionar hosting/TLS e banco somente após orçamento e requisitos de acesso remoto. Não migrar para cloud até fechar essas dependências humanas.

## Continuidade ? progresso das miss?es de autonomia/integra??es (2026-11-01)

Conclu?do no checkout local: ciclo de aprendizagem persistente; worker local recorrente; painel de intelig?ncia; pap?is internos estruturados; recupera??o Crossref; adaptadores Gemini/Tavily/Crossref/GitHub; snapshots GitHub read-only; embeddings opcionais; or?amento fail-closed por dia/tarefa; pesquisa e extra??o com proveni?ncia; documenta??o e testes simulados.

Pend?ncias para avan?ar sem falsa declara??o de prontid?o:
1. Configurar `.env` localmente com chaves autorizadas e selecionar Gemini sem enviar valores ao chat.
2. Rever pre?o/modelo Gemini no momento e configurar limites pequenos em UI; realizar teste real somente conforme aprova??o de gasto.
3. Configurar Tavily e habilitar explicitamente pesquisa global e por t?pico; fazer chamadas b?sicas primeiro devido a cr?ditos.
4. Adicionar indexa??o/reindexa??o sem?ntica em background apenas ap?s decis?o de or?amento; atualmente ? acionada por mem?ria espec?fica.
5. Evoluir detec??o de contradi??es e atualidade al?m de heur?sticas.
6. Testar sincroniza??o real GitHub/Crossref em repos/assuntos escolhidos; nenhum token necess?rio para reposit?rio p?blico.
7. Revisar threat model, backups e isolamento multiusu?rio antes de qualquer exposi??o remota; API continua loopback/user ?nico.
8. Executar a su?te completa ap?s as ?ltimas altera??es e validar inicializa??o sem chaves e com MockProvider.

## Continuity - ALL FOR ONE / initial routing (2026-11-01)

- Audit confirmed that chat provider selection remains manually persisted; automatic model routing is not yet connected to chat runtime.
- Added `nexus_learning/model_router.py`: pure deterministic policy for SIMPLE, STANDARD, ADVANCED and RESEARCH; filters availability, capability, context, cost and latency metadata; fallback stays within local/remote trust boundary.
- Fail-closed behavior: remote candidates require explicit remote permission and budget authorization; unavailable, disallowed, malformed or insufficient-context candidates are rejected.
- This policy is not yet wired into runtime provider choice. Model latency, price and capability metadata need a trusted catalog or reviewed configuration before automatic routing. Manual Ollama/Qwen selection remains unchanged.
- Product-agent roles remain sequential and deterministic, not independent LLM agents. Research, knowledge and memory infrastructure exist, but chat does not delegate model tool calls. No Gemini generation or Tavily search was run during this work.
- Initial integrity audit found numerous existing local changes; all preserved. `.env` and local database remain Git-ignored. No commit/push. Codex profiles passed static validation, but subagent startup failed because the local OAuth token had been invalidated after the user's logout; no global settings were changed.
- Verification: `python -m compileall -q nexus_learning tests` passed; `python -m unittest discover -s tests -v` passed with 97 tests, including 9 router tests; `git diff --check` passed.

## Added from the routing/research continuation (2026-11-01)

1. Implement native provider tool-call contracts and tool-result continuation (Ollama/OpenAI-compatible adapters only where capability is confirmed); require explicit human confirmation before cost-bearing research.
2. Add browser-driven E2E for confirmation rejection/acceptance, streaming, source-link rendering, and authenticated research history.
3. Evolve deterministic product-agent steps into separately budgeted specialist calls with typed envelopes, permission scope, timeout, concurrency caps, and independent reviewer; do not imply current roles are independent LLM agents.
4. Design isolated self-improvement proposals: separate workspace, explicit changed-file manifest, bounded test command allowlist, and promotion only after review.
5. Improve citation quality beyond reference-index validation; compare claims to excerpts and disclose unresolved contradiction/date gaps.
6. Add concurrency tests for multiple confirmed Tavily requests sharing the daily cap; verify reservation remains atomic.
## Update backlog — universal tool calling (2026-11-02)

**Implemented and locally tested:** normalized provider tool-call envelope; Ollama/OpenAI-compatible parsing and serialization; exact model capability allowlist; READ-only schemas; policy-gated execution; bounded arguments/results, rounds/calls/time; safe activity metadata; API authenticated continuation; budgeted remote continuation; tool-less cancellable SSE.

**Next, in order:**
1. Add native protocol implementations and simulated contract tests for Gemini and Anthropic before capability exposure.
2. Add cancellation-aware asynchronous generation so SSE can support tools without hidden work after disconnect.
3. Add a two-phase owner confirmation UI/API for model-requested SENSITIVE tools; never let the model approve its own action.
4. Add progress events in the interface for tools and agent steps.
5. Add runtime skills as proposed → owner-reviewed → approved, with bounded on-demand context and no permission elevation.
6. Add an isolated executor only with a concrete code/file tool, least-privilege mounts, no secret forwarding, resource/network limits, audit and owner review.
7. Evolve current sequential Architect/Analyst/Reviewer inference into budgeted role-specific orchestration; use concurrency only for independent tasks and preserve a separate reviewer gate.

Do not interpret provider protocol support as proof that every model supports tools; the exact model allowlist remains empty until manually verified.
