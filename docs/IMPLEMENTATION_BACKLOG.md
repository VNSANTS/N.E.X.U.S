# N.E.X.U.S. — Backlog técnico de implementação

**Data da revisão:** 2026-11-01
**Escopo:** revisão somente do repositório N.E.X.U.S.; não inclui Nexus Finance nem outros projetos.

Este documento é o plano operacional derivado do código e da documentação existentes. Ele separa o que está no repositório do que ainda depende de escolhas, credenciais ou execução no computador.

## 1. Estado verificado no código

| Área | Evidência no repositório | Estado real |
|---|---|---|
| Persistência | `nexus_learning/engine.py` | SQLite para memórias, fontes, afirmações, tarefas e auditoria |
| Ingestão | `nexus_learning/ingestion.py` | TXT/Markdown, hash, chunks e busca lexical; sem PDF, OCR ou embeddings |
| Pesquisa | `nexus_learning/crossref.py` | Metadados bibliográficos da Crossref; não baixa artigos nem valida afirmações |
| Política | `nexus_learning/policy.py` | Allowlist fail-closed para READ, WRITE_REVERSIBLE e SENSITIVE |
| Runtime | `nexus_learning/runtime.py` | Uma tarefa textual por vez usando um provider; sem ferramentas executáveis |
| Providers | `nexus_learning/providers/` | Contrato e MockProvider offline; nenhum provider remoto implementado |
| CLI | `nexus_learning/__main__.py` | Comandos locais de memória, fontes, afirmações, tarefas, ingestão, pesquisa e demonstração offline |
| Testes | `tests/` | unittest; execução CI anterior confirmada em Python 3.11 e 3.12 |
| API/web | Não existe implementação correspondente no tree atual | Pendente |
| Cloud/worker | Não existe implementação correspondente no tree atual | Pendente |

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
