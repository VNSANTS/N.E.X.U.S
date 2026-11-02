# Runtime, memory and Codex multiagent baseline audit — 2026-11-01

The findings below describe the state at the start of the local application implementation. See `docs/LOCAL_API.md` and the implementation addendum in `ARCHITECTURE.md` for capabilities added later the same date.

## Provider/runtime boundary

`ModelProvider` and `MockProvider` are in `nexus_learning/providers/`; the runtime receives a provider by injection. `TaskRuntime` is synchronous, calls `generate` with a 30-second timeout and 800-token output cap, persists task state/events, and has no tools. MockProvider remains the offline path. Provider-neutral error classes now define fixed safe codes and retryability; the runtime records only those fields and never exception text. Unknown exceptions retain type only.

The contract currently has no cancellation token, streaming, structured tool calls, provider catalog, normalized usage, or retry policy. `timeout=30` is a request to the adapter, not a runtime-enforced hard cancellation guarantee. Add cancellation only with a transport mechanism that can actually abort an in-flight request. Keep a single pinned provider/model, external configuration and secret source outside source control, and add adapters only after owner selection. Do not retry or silently fall back yet.

## Memory and learning

Implemented locally: episodic/semantic/procedural memories; sources and source-linked claims with review states; learning tasks and audit events; TXT/Markdown ingestion, chunk provenance and lexical search. Runtime tasks persist user input and model output, but the runtime does not retrieve memories, maintain conversation sessions, connect responses to sources, or write memory. There is no automatic promotion of generated output to fact.

Proposed integration: keep session history, personal memory, sourced knowledge, task state and audit as separate records. Retrieve only a small relevant set of active memories/validated claims, with IDs, provenance and trust labels. Treat retrieved or ingested text as untrusted input. A model may create a *proposal* for memory/claim with source and confidence rationale; deterministic validation and, where required, user review must approve it. Keep deletion, retention, consent, export and correction policy explicit before cloud sync. Never infer a fact from the model's answer alone.

## Six Codex project profiles

The six versioned profiles exist: orchestrator, architect, developer, researcher, tester and reviewer. Their instructions distinguish coordination, read-only analysis, bounded edits, official research, testing and independent review. TOML parses and names are distinct. Profiles do not set provider, auth, sandbox or approval policy. `.codex/config.toml` enables project agents with a maximum of four concurrent threads. These are development-time Codex roles; they are not the N.E.X.U.S. product's runtime agents and do not implement inter-agent messaging or shared context.


Product multiagent runtime remains unimplemented. Before enabling it, define agent scopes, typed task/message envelopes, a shared-context allowlist, conflict arbitration by the supervised primary agent, per-agent budgets/step limits, and permissions enforced outside model prompts. Agents must not grant one another privileges; all tool calls pass through the same policy and audit layer.

## Future infrastructure order

1. Owner chooses provider/model, data policy, cost ceiling, credential source and benchmark criteria.
2. Add adapter behind the existing contract, simulated contract/error tests, and configuration validation. Keep secrets in process environment or a selected secret manager; redact all logs.
3. Extend the local task model with session/message IDs, cancellation states and idempotency before adding workers.
4. Decide identity, session isolation, retention and hosting; implement a small authenticated API around the existing runtime.
5. Add an allowlisted tool registry and approval checks before any action execution.
6. Add a worker only for durable queued work; use leases, idempotency, bounded retries and outbound-only PC connectivity.
7. Build a small web UI against the API, then cloud sync with version/conflict handling and explicit data minimization.
8. Add health metrics, redacted structured logs, backup/restore and failure recovery before unattended operation.

Cloud provider, auth, hosting, retention and sync decisions remain owner choices. No service, credentials, worker, API, UI or cloud sync were created in this audit.
