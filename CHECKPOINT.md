# Development Checkpoint

Update this file at the end of every meaningful development session.

## Current state
- Project: N.E.X.U.S. — Neural Engine Expert Underground System.
- Stage: MVP specification drafted; local OpenJarvis validation and key decisions pending.
- Last completed: 46 Agent Skill directories confirmed; architecture v1 documented; official OpenJarvis source statically audited; MVP specification drafted.
- Runtime implementation in this repository: not started/verified.
- Repository visibility: public temporarily, by user's decision.

## Confirmed direction
Cloud-first assistant, optional local Ollama, text first, lightweight event-driven standby, bounded agents/tools, separate personal memory and sourced knowledge, validated learning and explicit approval for sensitive actions.

## OpenJarvis audit
- Upstream: https://github.com/open-jarvis/OpenJarvis
- Commit: `570d75425d50592d931bac7a17ce6b2621561c06`
- License: Apache-2.0.
- Static remote review only; no install, scripts, builds or tests executed.
- Do not modify the upstream checkout. N.E.X.U.S. stays in its own repository.
- Recommendation: selectively reuse interfaces/patterns after local validation, not adopt the whole framework blindly.
- Full report: `docs/audits/OPENJARVIS_AUDIT.md`.

## MVP proposal
- Text API + responsive web UI.
- One cloud provider, bounded orchestrator, one READ tool.
- Deterministic tool allowlist, policy, timeouts, budgets, structured logs.
- SQLite; no vector DB in MVP.
- Offline tests for success, failure, timeout, prompt injection, session isolation and secret leakage.
- No voice, scheduler, parallel agents, shell/code, remote MCP or sensitive actions yet.
- Full specification: `docs/MVP_SPEC.md`.

## Constraints
Development PC: Intel i5 first generation, 8 GB DDR3 RAM, HDD. Avoid large local models and heavyweight optional extras. Cloud provider and hosting are undecided.

## Next steps
1. On PC, compare local OpenJarvis checkout to the reviewed upstream commit.
2. Run a small offline test subset in an isolated environment; do not run install scripts or connect credentials.
3. Measure RAM, CPU and disk use.
4. Decide reuse boundary, cloud provider, authentication and hosting.
5. Implement the first vertical slice only after the above decisions.

## Session handoff template
Record date/time, inspected/changed files, tests and results, blockers, decisions, exact next action and commands/environment details needed to resume. Do not claim unverified work is complete.
