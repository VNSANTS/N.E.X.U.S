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
