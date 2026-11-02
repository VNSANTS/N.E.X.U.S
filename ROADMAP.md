# Roadmap

Phases are review gates, not date promises. Complete and review each phase before expanding scope.

## 0 — Audit and foundation
Audit the intended base code/OpenJarvis, license, dependencies, working modules and tests. Establish repository hygiene, audit Agent Skills and define a realistic architecture. **Exit:** reviewed code audit, skills audit and architecture baseline. (Remote static OpenJarvis audit completed; local validation remains.)

## 1 — Minimal reliable assistant
Create a clean app entry point, configuration, one text conversation path, provider abstraction, one working model provider, bounded orchestrator, allowlisted tools, structured safe logs and tests. **Exit:** a simple approved tool task works reliably.

## 2 — Memory and context
Separate conversation context from long-term user memory. Add consent-aware writes, provenance, relevance retrieval, correction and deletion controls. **Exit:** relevant context is retrieved predictably and protected.

## 3 — Agents and tools
Define agent/tool contracts, task planning, bounded delegation, cancellation, retries, per-tool permissions and audit trail. **Exit:** inspectable multi-step tasks run within limits.

## 4 — Learning and research
Add budgeted research, source metadata, claim extraction, deduplication, corroboration, conflict handling and user clarification for subjective topics. **Exit:** traceable, reviewable knowledge updates.

## 5 — Standby and proactive operation
Add scheduler/event bus, lightweight standby, per-job budgets, quiet hours, notifications, pause and emergency stop. **Exit:** scheduled tasks run safely and return to standby.

## 6 — Voice and interfaces
Add push-to-talk first, replaceable speech adapters and responsive browser/mobile UI with task progress and approvals. **Exit:** reliable user interaction and visibility.

## 7 — Controlled self-improvement
Evaluate changes against fixed tests, use isolated branches/sandboxes, present diffs and require approval before merge/deploy. **Exit:** improvements are measurable and reversible.

## Delivery rules
Prefer a small working vertical slice. Avoid premature microservices. Test and document every change. State expected costs before adding paid services. Never change production behavior or permissions without approval.


---

## Revisão de implantação — prioridade cloud core e PC worker

Esta divisão atualiza a ordem de implementação acima:

1. **Cloud core primeiro:** aplicação leve, autenticação de usuário único, conversa textual, provedor de IA com camada substituível, memória essencial, fila, permissões e cache compacto. O assistente básico deve continuar acessível com o PC desligado.
2. **PC worker depois:** processo local leve que inicia conexão autenticada de saída, recebe somente tarefas permitidas e envia heartbeat. Primeiro teste: receber um documento de exemplo, extrair texto, salvar localmente e devolver metadados/resumo.
3. **Aprendizado pesado no PC:** arquivo de fontes, ingestão, limpeza, deduplicação, indexação e comparação de evidências em lotes pequenos. Embeddings ficam opcionais.
4. **Sincronização:** somente conhecimento revisado/validado e resumos necessários são sincronizados para o cache da nuvem. Conflitos devem ser versionados; nunca sobrescrever silenciosamente.

Se o PC estiver desligado, tarefas locais ficam aguardando. Não expor shell remoto, não abrir portas públicas e não exigir modelos grandes no PC atual. A meta é custo obrigatório zero, sem cartão/cobrança automática; validar cotas, privacidade e disponibilidade dos serviços gratuitos antes de escolhê-los.


## Revisão — modelo local como auxiliar de aprendizado
No PC worker, adicionar um adaptador opcional para modelo local pequeno/quantizado. Começar com testes de viabilidade (RAM, velocidade, estabilidade e qualidade) antes de escolher modelo. Usá-lo para resumo, classificação, extração de candidatos e organização de documentos; nunca para validar sozinho conhecimento. Preservar fontes e incertezas, aplicar verificações e encaminhar casos complexos à nuvem quando permitido. O worker deve continuar funcionando sem modelo local. Trocar o modelo deve ser possível sem alterar o restante da arquitetura.


## Nova frente — motor de aprendizado inspirado na neurociência
Consultar `docs/LEARNING_ARCHITECTURE_NEUROSCIENCE.md`. A implementação deve começar por proveniência, estados de conhecimento, memórias episódica/semântica/procedural, avaliação e testes — antes de adicionar LLM local. O documento é uma proposta fundamentada em literatura, não implementação. Prioridade: Fase 0 (fundamentos) e Fase 1 (memória funcional), mantendo o PC fraco e o custo obrigatório zero como restrições.


## Marco de implementação — núcleo local inicial

Criado o pacote `nexus_learning` com SQLite, memórias por categoria, fontes, afirmações com estado de validação e fila priorizada. Testes iniciais foram adicionados em `tests/test_learning_engine.py`.

Próximas tarefas técnicas:
1. Executar os testes no ambiente real e corrigir incompatibilidades.
2. Completar CRUD, expiração, exportação e exclusão de memória.
3. Implementar ingestão segura de texto/documentos com limites.
4. Adicionar comparação de afirmações e detecção determinística de duplicatas.
5. Criar consolidação em lote com relatório de alterações, sem promoção automática.
6. Integrar adaptadores de modelos apenas após o núcleo ser testado.


## Próximo marco — validação e consolidação assistida

O núcleo agora tem pesquisa/arquivamento de memórias, consulta e revisão de afirmações, fontes/excertos, relatório de possíveis duplicatas e itens sem evidência, auditoria, CLI e testes em CI. Antes de conectar modelos ou ativar tarefas autônomas, confirmar o workflow do GitHub Actions e executar o pacote no PC. Depois: ingestão de documentos segura, deduplicação melhor, revisão de conflitos e consolidação com diff/exportação.


## Runtime e integração — próxima etapa

- [x] Contrato de provedor de IA independente.
- [x] Provedor mock offline para desenvolvimento/testes.
- [x] Política fail-closed e allowlist de ferramentas.
- [x] Runtime inicial com estados, persistência e trilha de eventos.
- [x] Handoff detalhado para o Codex CLI.
- [ ] Confirmar CI de todos os testes após o runtime.
- [ ] Adaptador real de modelo após escolha/credenciais.
- [ ] API HTTPS e autenticação.
- [ ] Worker de PC com conexão de saída, leases, cancelamento e sincronização.
- [ ] Interface web e implantação gratuita dentro das cotas disponíveis.

## Continuity - ALL FOR ONE / initial routing (2026-11-01)

- Audit confirmed that chat provider selection remains manually persisted; automatic model routing is not yet connected to chat runtime.
- Added `nexus_learning/model_router.py`: pure deterministic policy for SIMPLE, STANDARD, ADVANCED and RESEARCH; filters availability, capability, context, cost and latency metadata; fallback stays within local/remote trust boundary.
- Fail-closed behavior: remote candidates require explicit remote permission and budget authorization; unavailable, disallowed, malformed or insufficient-context candidates are rejected.
- This policy is not yet wired into runtime provider choice. Model latency, price and capability metadata need a trusted catalog or reviewed configuration before automatic routing. Manual Ollama/Qwen selection remains unchanged.
- Product-agent roles remain sequential and deterministic, not independent LLM agents. Research, knowledge and memory infrastructure exist, but chat does not delegate model tool calls. No Gemini generation or Tavily search was run during this work.
- Initial integrity audit found numerous existing local changes; all preserved. `.env` and local database remain Git-ignored. No commit/push. Codex profiles passed static validation, but subagent startup failed because the local OAuth token had been invalidated after the user's logout; no global settings were changed.
- Verification: `python -m compileall -q nexus_learning tests` passed; `python -m unittest discover -s tests -v` passed with 97 tests, including 9 router tests; `git diff --check` passed.

## Continuity status (2026-11-01)

Completed in this slice: runtime-bound automatic/manual model router; fail-closed remote budget preflight; same-lane fallback; confirmed Tavily research in chat with source persistence/citations/history; PolicyEngine-gated sensitive tool; citation reviewer; contextual memory remains injected.

Still ahead: provider-native tool calling and tool-result cycles, browser-level confirmation/source E2E, truly independent/budgeted LLM specialist agents, and isolated self-improvement proposals with verification.


## Provider validation checkpoint - 2026-11-01

- Gemini/OpenAI adapters and manual selection paths are covered with network mocks; OpenAI automatic routing is covered with an explicitly authorized test budget.
- Added a regression fix so an explicit NEXUS_REMOTE_PROVIDERS allowlist is enforced by provider_from_env, matching ProviderManager. Empty allowlist denies remote providers; missing variable retains compatibility with existing global-opt-in configurations.
- No real provider calls, credentials access, or credit usage occurred. Remote budgets and defaults were not changed.
- Verification: compileall passed; the full suite passed with 119 tests; git diff --check passed with an existing line-ending warning for README.md.
