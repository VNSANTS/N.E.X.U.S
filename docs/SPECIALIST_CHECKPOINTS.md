# Specialist pipeline checkpoints — design gate

**Status:** checkpoint store foundation implemented; pipeline/API integration and end-to-end resume remain pending.  
**Scope:** Architect → Analyst → Reviewer, before final response generation.


## Implementation progress

The first persistence slice now exists in `nexus_learning/checkpoint_store.py`:

- owner- and session-scoped run records with context hash and provider fingerprint;
- fixed Architect → Analyst → Reviewer stage rows;
- bounded typed deliverable validation (no arbitrary keys or raw prompt/response fields);
- SQLite `BEGIN IMMEDIATE` transitions and lease-token checks;
- stale running stages become `interrupted_unknown` when a new lease is acquired;
- ambiguous stages remain blocked until an explicit retry-confirmation call;
- attempt history is recorded when a failed stage is explicitly authorized for retry.

This is **not yet wired into** `SpecialistPipeline`, synchronous chat, SSE, or the UI. It does not yet provide a user-facing resume endpoint, provider/trust-lane revalidation, lease renewal, cancellation, or a complete cross-process fencing/expiry policy. Do not describe P2-01 as complete until those integrations and the full required test matrix pass.

## Why this is needed

The current specialist pipeline runs synchronously in the chat request. It emits metadata events and stops after the first failed stage, but it does not persist stage deliverables. A process restart therefore cannot safely continue from the last completed specialist.

The provider may have completed and billed a request even if the application lost the response. Retrying such a call automatically would create at-least-once execution and could duplicate cost or side effects. The current specialists are tool-less, but billing and provider-side request processing still matter.

## Required persistence model

Use owner-scoped rows keyed by the existing runtime `task_id`:

- `agent_pipeline_runs`: task_id, owner_id, session_id, state, selected tier, bounded context snapshot reference/hash, created_at, updated_at.
- `agent_pipeline_stages`: task_id, agent_id, sequence, state, provider, model, input_hash, bounded deliverable_json, error_code, started_at, completed_at.
- Unique constraint on (task_id, agent_id); foreign key to the run; indexes on (owner_id, state, updated_at).

Do not store API keys, raw provider exceptions, tool arguments/results, hidden reasoning, or unbounded prompt/response bodies. A completed stage stores only the typed, bounded public deliverable needed by the next specialist. The original user message already belongs to the runtime task; any context snapshot must be size-limited, owner-scoped, and treated as sensitive local data.

## Stage state machine

```text
pending -> running -> completed
                  -> failed_known
                  -> interrupted_unknown
```

- Persist `running` atomically immediately before a provider call.
- Persist `completed` and the bounded deliverable atomically after parsing/validation succeeds.
- A process restart must not turn an old `running` stage into `pending` automatically.
- A call whose outcome is ambiguous becomes `interrupted_unknown`; never retry it automatically.
- A known pre-call failure may be marked `failed_known`.
- Only completed stages may be skipped during an explicit resume.
- Resume is an owner-authorized action tied to the same task/session and original context snapshot. It must not silently create a new task or duplicate a completed stage.

## Resume authorization and billing

- Resume must be explicit; never automatic on server startup or chat retry.
- Before resuming, revalidate owner/session, provider allowlist, trust lane, model availability, current budget, task age, and all configured limits.
- The user must be told which stage is ambiguous and that retry may incur another provider charge. Ambiguous stages require a separate explicit retry confirmation; otherwise the run remains paused.
- Never change local/remote trust lane during resume. Never fallback to a provider with different privacy/retention characteristics.
- Keep the existing global deadline and maximum three specialist calls per run/resume attempt. Bound the number of resume attempts.
- Final response generation is a separate stage and must not run until all required specialist stages have completed and evidence filtering has succeeded.

## Atomicity and concurrency

- Claim a resume with `BEGIN IMMEDIATE` and a compare-and-swap state transition.
- Use a lease/fencing token so two API processes cannot resume the same run.
- Each stage completion update must check the current lease token and expected state.
- A stale process must not overwrite a newer checkpoint.
- Persist stage result and completion event in one transaction.

## Required tests before implementation is considered complete

1. Successful run persists each typed stage result and resumes without repeating completed calls.
2. Failure before provider invocation is retryable only after explicit resume.
3. Crash/ambiguous provider outcome is marked unknown and is not retried automatically.
4. Explicit retry requires confirmation and creates a new attempt record.
5. Two processes cannot claim the same resume; stale lease tokens cannot write.
6. Owner A cannot read, resume, or cancel owner B's pipeline.
7. Oversized or malformed checkpoint JSON fails closed and is never passed to a provider.
8. Provider/model changes or trust-lane changes block resume.
9. Budget is rechecked before any resumed remote call.
10. Final response cannot run with a missing/failed required stage.
11. Sync and SSE routes share the same persistence semantics.
12. No raw prompt, provider response, exception text, secret, or tool payload appears in activity metadata.

## Implementation order

1. Add repository/store and schema migration with owner isolation and compare-and-swap transitions.
2. Add pipeline callbacks for stage start/completion/failure; keep provider calls outside DB transactions.
3. Persist bounded typed deliverables only.
4. Add explicit authenticated resume/status API; no startup auto-recovery.
5. Integrate sync and SSE flows and UI status.
6. Add concurrency, restart, privacy, and billing-regression tests.
