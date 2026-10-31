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
