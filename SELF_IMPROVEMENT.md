# Controlled Self-Improvement

N.E.X.U.S. may detect recurring failures and propose improvements to prompts, tools, workflows, tests or documentation. It must not silently alter production code or permissions.

## Cycle
1. Detect a repeatable failure or inefficiency.
2. Gather evidence and formulate a testable hypothesis.
3. Define success criteria and regression risks.
4. Prepare a proposal in an isolated branch/worktree.
5. Run checks and tests in a sandbox.
6. Compare behavior against fixed test cases.
7. Present diff, rationale, risks and results.
8. Require explicit approval before merge/deploy.
9. Preserve rollback information and update documentation.

## Sandbox
No production credentials by default. Restrict filesystem/network access. Apply CPU, memory, disk and time limits. Prevent access to unrelated user data. Review dependencies and scrub logs.

## Never do autonomously
Change permissions/security policies, add integrations that share data, send messages as the user, make purchases/payments, delete important data, merge/deploy production code, or disable audit controls.

## Evaluation
Measure task success, error rate, latency, cost and user feedback. A model's assertion that a change is better is not evidence.
