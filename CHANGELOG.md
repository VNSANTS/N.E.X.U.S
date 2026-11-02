## 2026-11-01 - validacao segura de Gemini e Tavily

- Credenciais recebidas foram configuradas somente no `.env` local ignorado pelo Git; Gemini limitado pela allowlist `NEXUS_REMOTE_PROVIDERS=gemini`. Provedor de conversa permaneceu Ollama/Qwen.
- Gemini autenticado via API oficial de listagem de modelos: 46 modelos retornados e modelo configurado disponivel. Tavily autenticado via endpoint de uso: 0 creditos consumidos na verificacao.
- O endpoint autenticado de check do N.E.X.U.S. confirmou os dois servicos, sem chamada de geracao Gemini nem busca Tavily. Budget de inferencia segue desligado; pesquisa manual exige confirmacao e autonomia Tavily permanece desligada.
- Fontes oficiais: Gemini Models API (`https://ai.google.dev/api/rest/v1beta/models/list`) e Tavily Usage (`https://docs.tavily.com/documentation/api-reference/endpoint/usage`).

## 2026-11-01 - conversa real com Ollama e multiprovider

### Implementado
- Adaptador local Ollama com descoberta de versao/modelos, selecao persistente, contexto/geracao limitados, streaming e fechamento/cancelamento.
- ProviderManager com Ollama, OpenAI, Anthropic, Gemini, Groq, OpenRouter e MockProvider; status sem nomes/valores de credenciais e sem fallback silencioso.
- Interface de providers e conversa conectada a catalogo/modelos, teste de conexao, selecao e SSE; respostas concluidas preservam provedor/modelo no historico.

### Validacao
- Teste real loopback pela API autenticada com `qwen2.5:0.5b`: stream concluido e historico persistido. O modelo respondeu `3` a uma pergunta de 2+2; portanto a ligacao funciona, mas o modelo pequeno nao e confiavel para raciocinio.
- Provedores remotos nao foram testados com credenciais reais.
- A primeira execucao completa encontrou duas falhas de testes (catalogo publicava nomes de variaveis de segredo; expectativa do teste nao incluia temperatura). Corrigidas e verificadas em testes direcionados; repetir a suite completa antes de concluir.

## 2026-11-01 - ciclo continuo e integracoes locais

### Adicionado
- Ciclo SQLite persistente de dez fases, fila idempotente, recuperacao limitada, scheduler configuravel, controles API/UI, perguntas humanas e tarefas de aprofundamento.
- Crossref e Tavily como adaptadores de pesquisa; extracao limitada de paginas publicas, fontes registradas e conteudo externo marcado como nao confiavel.
- Gemini conectado ao runtime e a analise candidata; endpoint de embeddings e indice semantico opcional.
- GitHub REST somente leitura, repositorios acompanhados, snapshots/diferencas de commits e issues.
- Orcamento fail-closed de providers por dia e tarefa, cobrindo chamadas, tokens e valor; ledger de integracoes, carregador `.env` local e controles no painel.
- Script opcional de inicializacao do worker no logon do Windows; nao foi ativado.

### Validacao
- `python -m compileall -q nexus_learning tests`: passou.
- `python -m unittest discover -s tests -v`: 72 testes passaram.
- `git diff --check` e parse estatico do script PowerShell: passaram.
- Adaptadores foram testados com HTTP simulado. Chaves nao estavam disponiveis e chamadas reais nao foram feitas.
- Gemini segue desabilitado e orcamento remoto zero por padrao; Tavily exige aprovacao global/por topico e limites; conhecimento nao e promovido automaticamente.

# Changelog

## 2026-11-01 — aplicação local integrada

### Adicionado
- API JSON local WSGI com autenticação por senha e bearer token, sessões, histórico de chat, tarefas, fontes, claims, memórias, atividade e estado do provider.
- Interface web responsiva conectada à API para conversar e consultar sessões, tarefas, fila, agentes, memórias, fontes, claims, atividade, ferramentas e providers.
- Context retrieval lexical limitado de memórias ativas e claims validadas com fonte; nenhum resultado do modelo vira fato automaticamente.
- Adapters stdlib opcionais para Gemini, Groq e OpenRouter com timeout, redirects desabilitados, erros padronizados e opt-in remoto fail-closed.
- Tools READ allowlisted; nenhum shell/execução irrestrita.
- Fila local com prioridades, idempotência, programação pontual, leases com fencing token, retries limitados e cancelamento enquanto queued.
- Supervisão determinística de agentes de produto com envelopes/atividade estruturados, sem confundir com perfis Codex.
- `.env.example`, scripts PowerShell e guia `docs/LOCAL_API.md`.

### Verificação
- `python -m compileall -q nexus_learning tests`: passou.
- `python -m unittest discover -s tests -q`: **47 testes passaram** em Python 3.13.17.
- API HTTP/UI verificada em loopback com SQLite em memória; provider HTTP testado com transporte simulado; nenhuma chamada remota real.
- Comandos help do CLI/serve/worker e `git diff --check`: passaram. CI não executado nesta alteração.

## 2026-11-01 — preparação provider-neutral

### Adicionado
- Taxonomia padronizada e segura de erros de provider, incluindo rate limit com `retry_after` finito e não negativo.
- Metadados seguros de erro nos eventos do runtime, sem persistir mensagens brutas de exceção.
- Comparativo oficial Gemini/Groq/OpenRouter e auditoria de memória/runtime/multiagentes.

### Verificação
- `python -m compileall -q nexus_learning tests`: passou; `python -m unittest discover -s tests -v`: 31 testes passaram; validação TOML dos seis agentes e `git diff --check`: passaram.
- Nenhum provider foi selecionado; sem adapter remoto, credenciais, fallback ou serviço externo.

## 2026-11-01 — validação local e correção fail-closed

### Corrigido
- `PolicyEngine` agora exige `True` literal para aprovação de ações WRITE_REVERSIBLE e SENSITIVE; valores truthy como strings e inteiros não concedem permissão.
- A configuração `allow_reversible` agora rejeita valores que não sejam booleanos.
- Adicionado teste de regressão para aprovações e configuração não booleanas.
- `.gitignore` agora cobre logs, backups e artefatos temporários locais.

### Verificação
- `python -m compileall -q nexus_learning tests`: passou.
- `python -m unittest discover -s tests -v`: 28 testes passaram em Python 3.13.17.
- CLI, runtime MockProvider, ingestão e busca lexical foram verificados com um banco e arquivo fictício temporários. CI não foi executado para estas mudanças.
- O `debug.log` não rastreado preexistente foi preservado sem leitura ou alteração; agora corresponde à regra `*.log`.

## 2026-10-31 — núcleo local executável e endurecimento

### Adicionado
- Núcleo SQLite para memórias episódicas, semânticas e procedurais.
- Cadastro de fontes e afirmações com estados explícitos de revisão.
- Fila de tarefas com pontuação heurística explicável e auditoria.
- Ingestão de TXT/Markdown, hash SHA-256, divisão em trechos e busca lexical.
- Política de ferramentas fail-closed e runtime textual com MockProvider offline.
- Cliente de metadados bibliográficos Crossref.
- Testes automatizados e workflow GitHub Actions para Python 3.11 e 3.12.
- Backlog técnico com a ordem de implementação e dependências pendentes.

### Endurecido nesta revisão
- SQLite `:memory:` compartilhado entre conexões curtas.
- Reivindicação condicional de tarefas para impedir execução duplicada.
- Persistência de erros sem mensagens potencialmente sensíveis do provider.
- Validação dos limites do runtime e do formato essencial da resposta.
- Testes de regressão para os casos acima.
- Workflow com path filter corrigido, permissões mínimas, timeout e compilação.

### Ainda não implementado
- Provider remoto de IA.
- API HTTP, autenticação e interface web.
- Memória automaticamente integrada ao contexto de conversa.
- Ferramentas reais, agentes paralelos ou execução de comandos.
- Cloud core, worker PC, sincronização e deploy.
- Voz, scheduler contínuo, embeddings e execução autônoma.

### Verificação
CI confirmado: execução [41255344883](https://github.com/VNSANTS/N.E.X.U.S/actions/runs/41255344883) passou em Python 3.11 e 3.12, incluindo compileall e unittest, no commit `59356b7674ee97b9c2357871d2221e35f7e53b59`. Testes no computador local também permanecem pendentes.


## 2026-10-31 — ambiente Codex multiagente

### Adicionado
- Perfis de projeto `orchestrator`, `architect`, `developer`, `researcher`, `tester` e `reviewer` em `.codex/agents/`.
- Configuração de projeto `.codex/config.toml` com multiagentes ativados e limite máximo de quatro threads simultâneas.
- Instruções persistentes de delegação em `AGENTS.md`.
- Prompt mestre de preparação que verifica o ambiente, protege o checkout, instala/valida a configuração, audita o N.E.X.U.S., executa testes e avança trabalho local desbloqueado.

### Limites
- Esta é infraestrutura de desenvolvimento do Codex, não funcionalidade do runtime N.E.X.U.S.
- Os agentes herdam autenticação, provedor e permissões da sessão principal.
- Nenhum provedor externo, credencial, serviço pago, publicação ou deploy foi configurado.

## Continuity - ALL FOR ONE / initial routing (2026-11-01)

- Audit confirmed that chat provider selection remains manually persisted; automatic model routing is not yet connected to chat runtime.
- Added `nexus_learning/model_router.py`: pure deterministic policy for SIMPLE, STANDARD, ADVANCED and RESEARCH; filters availability, capability, context, cost and latency metadata; fallback stays within local/remote trust boundary.
- Fail-closed behavior: remote candidates require explicit remote permission and budget authorization; unavailable, disallowed, malformed or insufficient-context candidates are rejected.
- This policy is not yet wired into runtime provider choice. Model latency, price and capability metadata need a trusted catalog or reviewed configuration before automatic routing. Manual Ollama/Qwen selection remains unchanged.
- Product-agent roles remain sequential and deterministic, not independent LLM agents. Research, knowledge and memory infrastructure exist, but chat does not delegate model tool calls. No Gemini generation or Tavily search was run during this work.
- Initial integrity audit found numerous existing local changes; all preserved. `.env` and local database remain Git-ignored. No commit/push. Codex profiles passed static validation, but subagent startup failed because the local OAuth token had been invalidated after the user's logout; no global settings were changed.
- Verification: `python -m compileall -q nexus_learning tests` passed; `python -m unittest discover -s tests -v` passed with 97 tests, including 9 router tests; `git diff --check` passed.

## 2026-11-01 - integrated chat routing and confirmed Tavily research

- Connected manual/automatic model routing, live candidate validation, budget-aware selection, same-trust-lane fallback, and routing activity to both chat endpoints.
- Added confirmed chat research through a PolicyEngine-gated Tavily tool, provenance/session history, untrusted source context, citation review, and source links in the SSE UI.
- Added weather/current-research intent classification and reviewer tests. Full suite: 114 tests passed; compileall passed. No live search or remote model generation was used.


## 2026-11-01 - Gemini and OpenAI adapter coverage

- Added mocked SSE coverage for Gemini and OpenAI and a budget-gated automatic OpenAI routing test.
- Fixed provider_from_env to enforce an explicitly configured NEXUS_REMOTE_PROVIDERS allowlist; empty means deny all, absent preserves legacy opt-in behavior.
- Documented model discovery, local configuration, official API references, and the fact that API access is not necessarily free or unlimited.
- No real provider request or credential access was performed.
