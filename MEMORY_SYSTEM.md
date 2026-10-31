# Memory System

## Purpose
Retain useful user-approved context so the assistant does not repeatedly ask for the same information. Memory is not a transcript archive and should not store everything by default.

## Categories
- Preferences and interaction style.
- Ongoing projects and confirmed decisions.
- Stable context the user wants retained.
- Task continuity/checkpoints.
- Temporary context with expiry.

Personal memory is separate from general knowledge.

## Principles
Minimize collection; preserve dates and uncertainty; allow correction, exclusion and deletion; respect sensitive-data restrictions and consent; retrieve only relevant records; never expose private memory in public logs or repository files.

## Write policy
Store durable context only when useful, appropriate and permitted. Prefer concise structured summaries to raw conversation dumps. Mark facts as confirmed, tentative or outdated.

## Read policy
Use relevance thresholds. Prefer the latest explicit correction when facts conflict. Ask the user when ambiguity materially affects an action.

## User controls
The product should eventually support inspection, correction, export and deletion. Deletion should propagate to indexes, caches and derived summaries where feasible, with backup retention documented.

## Never store
Passwords, API keys, unnecessary sensitive data, unreviewed web claims, or temporary details after expiry.
