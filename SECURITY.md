# Security Policy

## Public repository warning
This repository is public for now. Treat all files and commit history as publicly readable.

## Never commit
API keys, tokens, passwords, private keys, cookies, real .env files, credential exports, private conversation dumps, personal records, local databases, backups, logs or screenshots containing sensitive information.

Use environment variables or a secret manager. Commit only sanitized examples with placeholder values.

## Minimum controls
- Least privilege for agents and tools.
- Authentication for remote APIs and interfaces.
- TLS in transit.
- Input validation, output handling and rate limits.
- Per-tool authorization and action-specific approvals.
- Timeouts, cancellation and spending limits.
- Sandboxed code execution and self-improvement.
- Audit logs without unnecessary sensitive content.
- Pinned dependencies and vulnerability review.
- Backup/recovery procedures and emergency stop.

## Require explicit approval
Sending/publishing as the user, financial activity, purchases, destructive operations, permission changes, external data sharing and production deployment.

## Before every push
- [ ] Inspect staged files and diffs.
- [ ] Check for secrets and personal data.
- [ ] Confirm .env, databases, logs and local config are ignored.
- [ ] Review dependency and license changes.
- [ ] Verify no private files were added.

## If a secret is exposed
Revoke/rotate immediately; deleting the file is insufficient. Assess exposure, remove from history where appropriate, review access and document the incident without publishing the secret. Report security issues privately to the owner.

## Continuity - ALL FOR ONE / initial routing (2026-11-01)

- Audit confirmed that chat provider selection remains manually persisted; automatic model routing is not yet connected to chat runtime.
- Added `nexus_learning/model_router.py`: pure deterministic policy for SIMPLE, STANDARD, ADVANCED and RESEARCH; filters availability, capability, context, cost and latency metadata; fallback stays within local/remote trust boundary.
- Fail-closed behavior: remote candidates require explicit remote permission and budget authorization; unavailable, disallowed, malformed or insufficient-context candidates are rejected.
- This policy is not yet wired into runtime provider choice. Model latency, price and capability metadata need a trusted catalog or reviewed configuration before automatic routing. Manual Ollama/Qwen selection remains unchanged.
- Product-agent roles remain sequential and deterministic, not independent LLM agents. Research, knowledge and memory infrastructure exist, but chat does not delegate model tool calls. No Gemini generation or Tavily search was run during this work.
- Initial integrity audit found numerous existing local changes; all preserved. `.env` and local database remain Git-ignored. No commit/push. Codex profiles passed static validation, but subagent startup failed because the local OAuth token had been invalidated after the user's logout; no global settings were changed.
- Verification: `python -m compileall -q nexus_learning tests` passed; `python -m unittest discover -s tests -v` passed with 97 tests, including 9 router tests; `git diff --check` passed.
