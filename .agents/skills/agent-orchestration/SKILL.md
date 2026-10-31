---
name: agent-orchestration
description: Design safe task routing, delegation, budgets, and result aggregation across N.E.X.U.S. agents.
---
# Agent Orchestration
- Use a central planner/router with explicit task contracts, allowed tools, budgets, deadlines, and stop conditions.
- Route by task capability, provider reliability, cost, latency, and privacy.
- Keep agents least-privileged and isolate untrusted input.
- Track parent/child tasks, provenance, retries, and cancellation.
- Aggregate results with conflict detection and verification; never assume majority vote equals truth.
- Require user approval for external side effects and sensitive operations.