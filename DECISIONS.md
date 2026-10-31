# Decision Log

Record decisions and status. Proposed options are not final until explicitly accepted.

## D-001 — Identity
**Status: accepted.** Name: **N.E.X.U.S.** Expansion: **Neural Engine Expert Underground System**. Preserve punctuation and wording.

## D-002 — Product direction
**Status: accepted.** Personal assistant that coordinates agents, uses tools, maintains memory and validated knowledge, learns from research/task outcomes and runs approved scheduled workflows.

## D-003 — Runtime
**Status: accepted target.** Cloud-first and accessible from mobile/browser. Local Ollama is optional.

## D-004 — Standby
**Status: accepted requirement.** Lightweight and event-driven; no continuous LLM reasoning while waiting.

## D-005 — Existing codebase
**Status: pending local validation.** Official OpenJarvis was reviewed remotely. Reuse only selected components after local checkout/version, dependency, test and license validation; do not modify upstream.

## D-006 — Stack and storage
**Status: proposed.** Python/FastAPI, Pydantic, pytest and SQLite for the first MVP; confirm local compatibility and hosting before implementation.

## D-007 — Learning
**Status: accepted.** System-level research, knowledge curation, memory, tool discovery and evaluated workflow improvement; do not claim permanent model-weight learning.

## D-008 — Safety
**Status: accepted.** Sensitive actions require explicit approval. Self-improvement is sandboxed, tested, reviewed and reversible.

## D-009 — Public repository
**Status: accepted temporarily.** Repository is public for now. Do not commit secrets or private user data.

## D-010 — Runtime architecture v1
**Status: proposed baseline for user review.** Start with a cloud-first modular monolith. The model interprets and proposes; deterministic runtime components enforce task states, budgets, permissions, tool allowlists and approvals. Keep agents as bounded internal roles initially, not independent privileged processes. Separate sessions, personal memory, sourced knowledge, tasks/approvals and operational audit data. Do not add vector search, always-on standby, voice, autonomous jobs or microservices to the first MVP without evidence that they are needed. See [ARCHITECTURE.md](ARCHITECTURE.md).

## D-011 — Initial execution scope
**Status: proposed baseline for user review.** First vertical slice: text interface, one approved model provider, bounded orchestrator, one safe READ tool, policy checks, structured logs and automated safety tests. No sensitive external actions. Confirm the actual stack and reuse candidates after the codebase audit.

## D-012 — OpenJarvis reuse boundary
**Status: proposed.** Keep OpenJarvis in its own upstream checkout and keep N.E.X.U.S. in this repository. Do not adopt the full framework by default. Evaluate small reusable contracts/adapters (inference, agent, tool, event/trace, SQLite retrieval) after local tests. See `docs/audits/OPENJARVIS_AUDIT.md`.

## D-013 — MVP scope
**Status: proposed.** Authenticated text API/web UI, one cloud model provider, bounded orchestration, one READ-only tool, SQLite, policy enforcement, budgets/timeouts, logs and offline safety tests. Defer voice, scheduler, parallel agents, shell/code execution, remote MCP, vector database and sensitive actions. See `docs/MVP_SPEC.md`.
