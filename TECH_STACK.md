# Technology Stack

Candidate choices only; the OpenJarvis audit may change them.

| Area | Candidate | Decision criteria |
|---|---|---|
| Backend/API | Python standard library WSGI (local MVP) | Zero dependency, direct integration with current synchronous runtime; replace/extend for hosted async concurrency only with explicit need |
| Orchestration | Python modules initially | Simplicity and testability |
| Model gateway | Provider adapters; evaluate gateway libraries | Multiple providers, cost and fallback |
| Local model | Ollama adapter | Optional development/fallback |
| Database | SQLite initially; PostgreSQL for hosted concurrency | Reliability and migration |
| Semantic retrieval | Add only when measured need exists | Avoid premature complexity |
| Frontend | Static responsive HTML/CSS/JS for local MVP; evaluate framework only when needed | Keep local install light and API-connected |
| Realtime | WebSockets or server-sent events | Task progress |
| Voice | Replaceable speech-to-text/text-to-speech adapters | Cost, latency, privacy, language |
| Jobs | Lightweight scheduler/worker | Durable execution and retries |
| Tests | unittest plus WSGI/API integration tests | Repeatability without extra runtime dependency |
| Packaging | venv, pinned dependencies; containers if useful | Reproducibility on constrained PC |

## Provider strategy
Support multiple providers behind one interface. Route simple work to cheaper models and complex work to stronger models when appropriate. Track usage, latency, failures and estimated cost. Do not silently switch to providers with materially different privacy or cost terms. Keep API keys out of source control.

## Local development
Local inference is optional. Use mocks in tests. Avoid heavy services on the 8 GB PC unless needed. Keep only placeholder values in .env.example and ignore actual .env files. Determine supported versions after inspecting OpenJarvis.

## Decisions pending
Backend/frontend reuse, model gateway, database, hosting, speech services, authentication and vector search.
