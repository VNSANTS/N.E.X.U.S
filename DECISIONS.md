# Decision Log

Record decisions and status. Proposed options are not final until explicitly accepted.

## D-001 — Identity
**Status: accepted.** Name: **N.E.X.U.S.** Expansion: **Neural Engine Expert Underground System**. Preserve punctuation and wording.

## D-002 — Product direction
**Status: accepted.** Personal assistant that coordinates agents, uses tools, maintains memory and validated knowledge, learns from research/task outcomes and runs approved scheduled workflows.

## D-003 — Runtime
**Status: accepted target.** Cloud-first and accessible from mobile/browser. Local Ollama is optional.

## D-004 — Standby
**Status: accepted requirement.** Lightweight and event-driven; no continuous LLM reasoning while waiting.

## D-005 — Existing codebase
**Status: pending audit.** Inspect OpenJarvis and reuse working components where appropriate; do not rewrite before understanding it.

## D-006 — Stack and storage
**Status: pending audit.** Candidates include Python/FastAPI, reuse of existing UI, SQLite initially and PostgreSQL for hosted concurrency. Validate against actual code and requirements.

## D-007 — Learning
**Status: accepted.** System-level research, knowledge curation, memory, tool discovery and evaluated workflow improvement; do not claim permanent model-weight learning.

## D-008 — Safety
**Status: accepted.** Sensitive actions require explicit approval. Self-improvement is sandboxed, tested, reviewed and reversible.

## D-009 — Public repository
**Status: accepted temporarily.** Repository is public for now. Do not commit secrets or private user data. Revisit visibility before adding sensitive project artifacts.

## D-010 — Runtime architecture v1
**Status: proposed baseline for user review.** Start with a cloud-first modular monolith. The model interprets and proposes; deterministic runtime components enforce task states, budgets, permissions, tool allowlists and approvals. Keep agents as bounded internal roles initially, not independent privileged processes. Separate sessions, personal memory, sourced knowledge, tasks/approvals and operational audit data. Do not add vector search, always-on standby, voice, autonomous jobs or microservices to the first MVP without evidence that they are needed. See [ARCHITECTURE.md](ARCHITECTURE.md).

## D-011 — Initial execution scope
**Status: proposed baseline for user review.** First vertical slice: text interface, one approved model provider, bounded orchestrator, one safe READ tool, policy checks, structured logs and automated safety tests. No sensitive external actions. Confirm the actual stack and reuse candidates after the codebase audit.
