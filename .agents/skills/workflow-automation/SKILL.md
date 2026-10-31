---
name: workflow-automation
description: Design reliable event-driven workflows and scheduled tasks for N.E.X.U.S.
---
# Workflow Automation
- Model workflows as explicit states, triggers, actions, retries, timeouts, and compensating steps.
- Default to event-driven standby; do not run continuous LLM reasoning without a justified need.
- Use idempotency keys, bounded retries, deduplication, and durable audit logs.
- Preview actions and require explicit approval for messages, purchases, financial operations, deletion, permissions, or production deployments.
- Add kill switch, pause/resume, rate limits, and notification on failure.
- Test failure, duplicate events, partial completion, and recovery paths.