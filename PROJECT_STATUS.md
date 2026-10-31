# Project Status

**Stage:** MVP specification drafted; local OpenJarvis validation and key decisions pending.  
**Implementation:** no N.E.X.U.S. runtime implementation has been verified in this repository.

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
Validate the local OpenJarvis checkout against the audited upstream commit, run a carefully selected offline test subset, measure resource use, then finalize provider/authentication/hosting choices and MVP contracts.

## Open risks
- The local OpenJarvis folder may differ from the remote commit audited.
- OpenJarvis security capabilities require deliberate profile/configuration; do not rely on permissive defaults.
- Cloud inference and hosting can create recurring costs.
- Public repository: never commit secrets, private conversation exports, credentials or personal records.


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
