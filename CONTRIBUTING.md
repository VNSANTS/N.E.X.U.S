# Contributing and Development Workflow

This is a personal project. Human contributors and coding agents must follow these rules.

## Before editing
Read README, PROJECT_STATUS, ROADMAP, ARCHITECTURE, TECH_STACK, DECISIONS and CHECKPOINT. Inspect relevant code/tests. Confirm scope and milestone. Check licenses and attribution for reused code. Propose a plan for non-trivial changes.

## Development rules
- Make small, reviewable changes.
- Preserve working behavior unless a change is intentional.
- Verify capabilities in source/tests; do not invent them.
- Keep clear module boundaries.
- Add tests for fixes and new behavior.
- Handle errors, timeouts and cancellation.
- Keep secrets out of code and logs.
- Update docs when behavior or architecture changes.
- Avoid unnecessary dependencies.
- Never overwrite user work or run destructive commands without permission.

## Coding agents
Audit before broad changes. Report files inspected and tests run. Separate verified facts from assumptions. Avoid unrelated refactors. Never expose credentials. Stop and ask before permission changes, deployment, data deletion or external actions.

## Session closeout
Update CHANGELOG when appropriate and always update CHECKPOINT with exact state and next task. Explain any uncommitted changes.
