# Project Status

**Stage:** architecture v1 drafted; awaiting user review.  
**Implementation:** no N.E.X.U.S. runtime implementation has been verified in this repository.

## Completed
- Skills inventory and documentary triage: 46 directories with `SKILL.md` confirmed; see [docs/skills/FINAL_AUDIT.md](docs/skills/FINAL_AUDIT.md).
- Logical runtime architecture v1 drafted in [ARCHITECTURE.md](ARCHITECTURE.md).

## Confirmed direction
- Personal AI assistant beyond a conventional chatbot.
- Cloud-first runtime accessible from phone/browser.
- Local Ollama is optional, not a hard requirement.
- Interactive activation by text, button or voice.
- Lightweight event-driven standby; no continuous LLM reasoning loop.
- Approved scheduled and event-triggered task execution.
- Modular agents, tools and multi-provider model routing.
- Separate personal memory and sourced knowledge.
- Learning through research, validation, user clarification and evaluated workflows.
- Explicit approval for sensitive actions; sandboxed self-improvement.

## Architecture baseline proposed
- Modular monolith before microservices.
- Model proposes; runtime enforces permissions, budgets and execution.
- Bounded orchestrator and agents with explicit contracts.
- Tool allowlist, least privilege and action-specific approvals.
- Separate sessions, personal memory, knowledge, tasks and audit records.
- First MVP: text conversation, one model provider, one safe READ tool, policy checks, logs and tests.
- Voice, scheduled jobs, multi-agent parallelism, vector database and self-modifying code are later phases.

## Environment constraints
Development PC reported: Intel i5 first generation, 8 GB DDR3 RAM, HDD. Avoid requiring large local models. Cloud hosting and model costs are not selected.

## Next milestone
Define and approve the smallest executable MVP. Before implementation, audit the actual codebase/OpenJarvis intended for reuse, confirm stack and dependencies, then write task contracts and acceptance tests.

## Open risks
- OpenJarvis version, capabilities and license still need verification before reuse.
- Cloud model usage can create recurring costs; background jobs need budgets.
- Learning must not be misrepresented as permanent model-weight training.
- Public repository: never commit secrets, private conversation exports, credentials or personal records.
