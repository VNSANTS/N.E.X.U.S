# Architecture

## Principles
- Modular monolith first; split services only when justified.
- Cloud-first model inference; optional local adapters.
- Event-driven standby, not continuous LLM reasoning.
- Least privilege for tools and agents.
- Separate conversations, personal memory, knowledge and operational logs.
- Observable, attributable actions; replaceable providers and interfaces.

## Logical components
1. **Interaction layer:** text/voice input, task status, notifications and approvals.
2. **Orchestrator:** classifies requests, plans bounded tasks, coordinates agents, handles cancellation and returns results.
3. **Model gateway:** provider abstraction, capability routing, budgets, timeouts, retries and fallback.
4. **Agent runtime:** specialized workers with declared inputs, outputs, tools, budgets and time limits.
5. **Tool registry:** typed schemas, descriptions, permissions and audit hooks.
6. **Memory service:** user-approved personal context, summaries, correction and deletion.
7. **Knowledge service:** sourced claims, research notes, confidence, status and provenance.
8. **Learning engine:** research, comparison, validation and improvement proposals.
9. **Scheduler/event bus:** bounded time- or event-triggered jobs.
10. **Policy/approval service:** allow, require confirmation or deny.
11. **Observability:** structured logs, traces, metrics and audit events without secrets.

## Interactive request flow
Activation → session/context retrieval → task classification → planning → policy check → approval if needed → bounded agent/tool execution → result verification → user response → optional approved memory/knowledge update.

## Standby and jobs
A lightweight scheduler listens for approved triggers. A trigger creates a task; it does not grant permissions. Every job has allowed tools, duration and spend limits, cancellation and notification rules. Ambiguous or failed jobs stop safely.

## Data boundaries
- Conversation: transient messages and bounded summaries.
- Personal memory: user-specific context with consent and controls.
- Knowledge: researched claims with provenance.
- Operations: task states, schedules and audit events.
- Secrets: environment or secret manager only, never repository files.

## Deployment direction
Local computer is a development station, not assumed production inference host. A hosted API, database and optional worker are likely enough initially. Exact hosting and topology follow the audit and cost comparison.
