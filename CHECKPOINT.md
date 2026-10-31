# Development Checkpoint

Update this file at the end of every meaningful development session.

## Current state
- Project: N.E.X.U.S. — Neural Engine Expert Underground System.
- Stage: architecture v1 drafted; awaiting user review.
- Last completed: 46 Agent Skill directories confirmed in `.agents/skills/`; consolidated audit published at `docs/skills/FINAL_AUDIT.md`; logical runtime architecture v1 drafted in `ARCHITECTURE.md`.
- Runtime implementation in this repository: not started/verified.
- Repository visibility: public temporarily, by user's decision.

## Confirmed direction
Personal assistant beyond chatbot; cloud-first runtime; optional local Ollama; interactive text/button/voice; lightweight event-driven standby; approved scheduled tasks; modular agents/tools/provider routing; separate personal memory and sourced knowledge; validated learning; explicit approval for sensitive actions.

## Architecture v1 proposal
- Modular monolith; avoid premature microservices.
- Model interprets and proposes; deterministic runtime enforces policy and execution.
- Bounded orchestrator, agent contracts, tool allowlist, budgets, timeout and cancellation.
- Separate sessions, personal memory, sourced knowledge, tasks/approvals and operational audit.
- MVP proposal: text, one provider, one safe READ tool, policy checks, structured logs and safety tests.
- Voice, scheduler, parallel agents, vector search and self-improvement remain out of first MVP.

## Skills status
- 46 directories with `SKILL.md` confirmed on main.
- 10 are internal procedural guides; the remainder are imported development skills.
- One new Cloudflare `security-audit` skill was added during the consolidated audit, with MIT license.
- Scripts of third-party skills have not been executed.
- MCP servers, SAST CLIs, browser test runtimes, external voice APIs and other host tools are not installed by this audit.
- See `docs/skills/FINAL_AUDIT.md` for the full decisions and remaining blockers.

## Constraints
Development PC: Intel i5 first generation, 8 GB DDR3 RAM, HDD. Avoid requiring large local models. Provider costs and hosting remain undecided. Any local sandbox must be validated on the PC; do not assume it exists.

## Next steps
1. Review and approve/correct architecture v1.
2. Audit OpenJarvis/source code intended for reuse, including license, dependencies and working features.
3. Define MVP contracts, task states, API and acceptance tests.
4. Decide initial provider, authentication, database and hosting with cost/privacy comparison.
5. Implement one small vertical slice and verify it before expanding.

## Session handoff template
Record date/time, inspected/changed files, tests and results, blockers, decisions, exact next action and commands/environment details needed to resume. Do not claim unverified work is complete.
