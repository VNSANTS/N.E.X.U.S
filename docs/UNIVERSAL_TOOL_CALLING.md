# Universal tool calling

## Current implementation

The conversation runtime has a provider-neutral `ToolCall` contract. A model call can return text plus structured calls; the runtime can then make another bounded model request with the result. The implementation is deliberately narrower than the set of tools exposed by the API:

1. `ToolRegistry.model_tools()` publishes JSON Schema declarations for READ tools only.
2. The API enables native tool calls only for an exact, explicitly configured `provider:model` pair in `NEXUS_TOOL_CALLING_MODELS`.
3. Every call is validated against the code-owned registry and executed through `ToolRegistry.execute()` and `PolicyEngine`.
4. Only JSON-safe, bounded results return to the model, labelled as untrusted data.
5. Tool names and status are audited; arguments, result bodies and provider exception text are not written to activity logs or chat history.

Current READ tools: `memory.search` (personal memory) and `knowledge.claims` (claims by review state). Tavily `research.search` stays SENSITIVE and is not exposed to model-native calls; the existing request-level owner confirmation flow controls it. No shell, arbitrary file access, communications or mutation tools are exposed.

## Enablement

Native protocol support is implemented for Ollama `/api/chat` and OpenAI-compatible Chat Completions adapters (OpenAI, Groq and OpenRouter). Protocol support alone does not establish support in every model. Verify an exact model's tool-call capability first, then add its exact identifier to local `.env`:

```dotenv
NEXUS_TOOL_CALLING_MODELS=ollama:qwen2.5:0.5b,openai:<verified-model-id>
```

The setting is empty in `.env.example`. Gemini and Anthropic adapters remain text-only; the runtime does not advertise tools to them.

Each task is bounded to four tool rounds, eight calls and 180 seconds of total tool-cycle time. Individual model calls are also bounded by the provider timeout; existing remote budget reservations apply to each generation including tool schemas and continuations. Arguments and serialized results are limited to 8 KB. These limits are code defaults, not a configurable financial budget.

SSE keeps provider-native streaming and cancellation. Since the current urllib generation transport cannot interrupt an in-flight non-streaming call, the runtime does not advertise tools on SSE. Use the authenticated non-streaming conversation endpoint for tool-capable models until a cancellable provider tool-call transport is implemented. No real provider calls were made in validation.

## Compatibility and roadmap

Text-only providers and `MockProvider` preserve the existing contract. Streaming remains unchanged. OpenAI-compatible adapters serialize canonical assistant tool calls and tool-result messages; Ollama serializes its native assistant calls and `tool_name` result messages. Ollama omits call IDs in its response, so the adapter creates fresh per-response IDs.

Next increments should add native tool-cycle tests for each adapter before advertising model support; then add owner-confirmed research as a two-phase tool approval, richer JSON Schema constraints, cancellation-aware async transport, and event-stream activity notifications. Do not allow a model to approve its own SENSITIVE call.

## Architectural references

The local comparative review named in the 2026-11-02 mission was not present in this checkout. Its copy was read from the open source branch of [PR #2](https://github.com/VNSANTS/N.E.X.U.S/pull/2); it recommends this order: safe tool loop, typed specialist agents, evidence review, then owner-reviewed procedural skills and isolated execution.

The implementation preserves N.E.X.U.S.'s Python/SQLite runtime. Hermes Agent suggests bounded curated memory and on-demand skills; OpenClaw separates tool policy from execution sandbox; NanoClaw provides patterns for per-task container isolation. Those projects are references, not dependencies or runtime components. We are not adding a sandbox until code/file execution is an approved, concrete requirement.

Official references reviewed 2026-11-02:
- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [Anthropic tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- [Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [OpenClaw sandbox versus tool policy](https://docs.openclaw.ai/gateway/sandbox-vs-tool-policy-vs-elevated)
- [NanoClaw security](https://github.com/nanocoai/nanoclaw/blob/main/docs/SECURITY.md)
- [Hermes memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)
