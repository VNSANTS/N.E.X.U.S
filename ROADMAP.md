# Roadmap

Phases are review gates, not date promises. Complete and review each phase before expanding scope.

## 0 — Audit and foundation
Audit the intended base code/OpenJarvis, license, dependencies, working modules and tests. Establish repository hygiene, audit Agent Skills and define a realistic architecture. **Exit:** reviewed code audit, skills audit and architecture baseline.

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
