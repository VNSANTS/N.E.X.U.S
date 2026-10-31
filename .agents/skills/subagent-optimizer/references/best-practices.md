# Claude Code subagent and Codex custom agent best practices

Distilled from the official docs (https://code.claude.com/docs/en/sub-agents,
.../tools-reference, .../costs) and the API tool-search docs
(https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool),
checked 2026-09. Each rule is checkable against one agent file. Severity in
brackets. The scan script raises codes in CAPS; this file explains the *why* and
the fix. Claude Code's own `/doctor` reports unused skills, MCP servers and plugins
against their context cost; it does not look at agents, which is the gap this
skill fills.

## Why this matters (token economy)

- A subagent starts fresh: its system prompt + tool schemas + the full CLAUDE.md
  hierarchy + a git snapshot load **on every launch**. Bloat is paid per
  invocation and multiplied across parallel/chained agents.
- What the scanner measures is definition text only (frontmatter + body, chars/4).
  Tool schemas, inherited CLAUDE.md, skills and memory are outside it, so its totals
  rank agents and show a before/after of the file; they are not launch cost.
- Tool definitions are the dominant avoidable cost. Anthropic's tool-search docs
  put a typical multi-server MCP setup at **~55k tokens** of definitions and report
  **over 85%** saved by loading only the tools a task needs. Claude Code defers MCP
  definitions by default; built-in schemas are what an unrestricted agent still pays for.
- It's not only cost: the same docs note tool-selection **accuracy degrades as the
  tool list grows** (tens of tools). A tight allowlist makes the agent *more correct*,
  not just cheaper.
- The scanner's trim point (`MANY_TOOLS`) is more than 10 tools on one agent: a
  single-purpose agent rarely needs more, and every extra schema costs tokens and
  selection accuracy.
- An agent's *result* also costs the parent's context — instruct a concise summary,
  not a dump.

## Frontmatter

**tools**
- `[high] NO_TOOLS_FIELD` — omitting `tools` inherits ALL tools. Always propose an
  explicit minimal allowlist (see tool-catalog.md). This is the headline win.
- `[high] WRITE_ON_READONLY` — `Edit`/`Write`/`NotebookEdit` on an agent whose body
  declares it doesn't write code contradicts that mandate. Drop them unless the body
  truly writes (e.g. an architect that persists a plan file — then keep only `Write`).
  **Memory exception:** an agent with `memory:` set legitimately needs `Edit` **and**
  `Write` to maintain its `MEMORY.md` and topic files — the harness instructs it to
  "use the Write and Edit tools to update your memory files." Never strip `Edit`/`Write`
  from a memory-enabled agent; doing so silently breaks memory upkeep. `NotebookEdit`
  is still droppable (memory files are Markdown, not notebooks).
- `[med] DEAD_TOOL_ENTRY` — tools on the documented subagent blacklist
  (`AskUserQuestion`, `EndConversation`, `EnterPlanMode`, `ScheduleWakeup`, `TaskOutput`,
  `WaitForMcpServers`, `Workflow`, and `ExitPlanMode` unless the agent sets
  `permissionMode: plan`, which the scanner checks). Remove.
- `[med] LEGACY_TOOL_NAME` — a name from an older release (`Task`, `LS`, `MultiEdit`,
  `NotebookRead`, `BashOutput`, `KillShell`). Rename to the current tool after checking
  the installed version.
- `[low] NESTED_AGENT_TOOL` — lists `Agent`. Nested subagents are on by default, so this
  is legitimate for an agent that delegates; it is dead at the depth limit or with
  nesting off. Ask keep-or-drop; never strip silently (see tool-catalog.md).
- `[low] BACKGROUND_STRIPPED` — a tool the harness removes from background subagents
  (`TaskCreate`/`TaskGet`/`TaskUpdate`/`TaskList`, `ListAgents`, `LSP`, MCP resource
  tools). Only useful if the agent is launched in the foreground.
- `[med] MANY_TOOLS` — >10 entries on a single-purpose agent; trim to what the body
  uses, or use `disallowedTools` if intent is "all except writes".
- `[med]` Bash needed only for narrow ops (read-only git, SQL) → keep `Bash` but
  recommend scoping destructive commands via `Bash(...)` permission rules or a
  `PreToolUse` hook rather than widening.

**description** (loads session-wide for routing — keep it earning its tokens)
- `[med] WEAK_TRIGGER` — role-only ("Reviews code") under-triggers. Name concrete
  conditions: "use when…", "after…", "whenever…".
- For agents meant to fire automatically, include a proactive cue: "use proactively"
  / "use immediately after…".
- `[low] LONG_DESCRIPTION` — multi-screen escaped-`\n` example blocks inflate every
  session. Keep the triggers + 1–2 tight examples; cut the rest.

**model** (defaults to `inherit` when omitted)
- `[low] MODEL_INHERIT` — fine if intentional. But pin `haiku` for mechanical
  agents, and pin `sonnet`/`opus`/`fable` for agents whose competence requirement is
  fixed regardless of session model (don't let a planner end up on Haiku).
- A mechanical agent on `opus` is a downgrade candidate; a read-only agent is not
  automatically one (security review, architecture analysis). Any model change is a
  candidate until compared on the agent's real task.
- Haiku lacks MCP tool-search (`tool_reference`); a Haiku agent relying on many
  deferred MCP tools won't get on-demand loading.

**effort** (inherits the session's level when omitted; recommend it with the model)

Checked 2026-09-24 against the subagent docs, Claude Code's model configuration page
(https://code.claude.com/docs/en/model-config#adjust-effort-level) and the API effort
page (https://platform.claude.com/docs/en/build-with-claude/effort).

- `[low] EFFORT_INHERIT` — no `effort`, so the agent runs at whatever level the
  session uses. Fine if intentional; pin it when the job's depth is fixed. Not raised
  on a Haiku model, which has no effort levels.
- `[low] EFFORT_UNSUPPORTED` — `effort` set on a Haiku model. The model
  configuration page lists the models that take effort and says "Models not listed
  here do not support effort"
  (https://code.claude.com/docs/en/model-config#adjust-effort-level); Haiku is not
  listed, so the pinned model does not support effort. This is a note, not a rule:
  "the per-invocation `model` parameter" comes first in the subagent model order
  (https://code.claude.com/docs/en/sub-agents#choose-a-model), so a call can still
  run the agent on a model that takes effort. The scanner treats any model value containing "haiku" (the
  alias or a full ID) this way; `inherit` and other IDs get the ordinary checks.
- `[med] EFFORT_INVALID` — a value outside `low`, `medium`, `high`, `xhigh`, `max`.
- `[low] HIGH_EFFORT_READONLY` — `xhigh` or `max` on an agent whose tools are
  read-only (no `Edit`, `Write`, `NotebookEdit` or `Bash`). Ask whether the job needs
  it; a lower level is a candidate, not a finding.
- Levels depend on the model. Claude Code lists all five for Fable 5.1/5, Opus
  5.5/5/4.8/4.7 and Sonnet 5, drops `xhigh` on Opus 4.6 and Sonnet 4.6, and says
  "Models not listed here do not support effort" (Haiku is not listed). An
  unsupported level falls back to "the highest supported level at or below the one
  you set". Frontmatter overrides the session level but not the
  `CLAUDE_CODE_EFFORT_LEVEL` environment variable, and `maxEffortLevel` or an
  organization cap still applies.
- The API page's typical uses: `low` for "Simpler tasks that need the best speed and
  lowest costs, such as subagents"; `medium` for "Agentic tasks that require a
  balance of speed, cost, and performance"; `high` for "Complex reasoning, difficult
  coding problems, agentic tasks"; `xhigh` for "Long-running agentic and coding tasks
  (over 30 minutes) with token budgets in the millions"; `max` for "Tasks requiring
  the deepest possible reasoning and most thorough analysis".
- Mapped to archetypes: read-only search or filter workers, `haiku` with no `effort`
  field or a larger model at low or medium; implementation workers, medium;
  planners, architects, and reviewer or security agents that trace complex logic, a
  strong model at high; `xhigh`/`max` only for long-running or hardest work the user
  confirms. The API page says to "Evaluate performance on your specific
  use cases before deploying", so any change is a candidate to verify on the agent's
  real task.
- Codex custom agents use different keys and levels; see the Codex section below.

**name / hygiene**
- `[med] NAME_FORMAT` — must be lowercase-hyphenated, unique in its scope (a
  duplicate name in the same scope is silently discarded).
- Only `name` and `description` are required. Documented optional fields: `tools`,
  `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`,
  `hooks`, `memory`, `background`, `omitClaudeMd`, `effort`, `isolation`, `color`,
  `initialPrompt`, `experimental`. Anything else is a typo or a leftover.

## Body (system prompt)

- `[high]` **Single responsibility** — one agent, one job. "Writes AND reviews AND
  commits" should be split. Reward explicit negative scoping ("only X; does not Y").
- `[high]` **No CLAUDE.md duplication** — custom subagents inherit the CLAUDE.md
  hierarchy unless `omitClaudeMd: true` is set. Re-pasting rules that are provably
  inherited is dead weight; a rule you cannot find in a loaded CLAUDE.md is not a
  duplicate, and on an `omitClaudeMd` agent (`[info] OMITS_CLAUDE_MD`) the body may be
  the only place those rules exist. Locate the source before cutting.
- `[med] MEMORY_BOILERPLATE` — when `memory:` is set, the harness auto-injects memory
  read/write instructions + the top of `MEMORY.md`. A hand-written "Persistent Agent
  Memory" section (often ~45 lines, and identical across an author's agents) largely
  duplicates that. Trim to a one-line "update your memory as you learn".
- `[med] LONG_BODY` — official single-purpose examples run ~25–45 lines; >150 is
  likely bloated. Target shape: one-line role → numbered "when invoked" steps →
  focused checklist → explicit output format → short closing principle.
- `[low] NO_OUTPUT_FORMAT` — add an output-format / "return a concise summary"
  section so results don't flood the parent.
- `[low] EMPHASIS_DENSITY` — heavy ALL-CAPS MUST/NEVER reads as nagging and rarely
  helps. Explain the *why*; reserve emphasis for the one or two real footguns.
- `[low]` References to local-only working files the agent won't have at runtime → fix.

## Codex custom agents (`.codex/agents/*.toml`)

Checked 2026-09-24 against https://learn.chatgpt.com/docs/agent-configuration/subagents,
https://learn.chatgpt.com/docs/models and
https://learn.chatgpt.com/docs/config-file/config-reference. Quotes below are from
those pages. What Codex's own code applies or rejects is reported from a reading of
openai/codex at release rust-v0.156.1 (https://github.com/openai/codex/tree/rust-v0.156.1)
and is marked "reported" with the file; where it differs from the docs, the code is
what runs, on that release.

**Format**
- "add standalone TOML files under `~/.codex/agents/` for personal agents or
  `.codex/agents/` for project-scoped agents." "Each file defines one custom agent."
  Custom agents are a local-client feature ("In local Codex clients, you can also
  define custom agents"); don't claim they run in Codex cloud.
- Every standalone custom agent file "must define" `name`, `description` and
  `developer_instructions`, and "the `name` field is the source of truth", not the
  filename. The docs' own names use underscores (`pr_explorer`), so `NAME_FORMAT`
  does not apply.
- A role can also be declared in `config.toml` as an `[agents.<name>]` table whose
  `config_file` is "Path to a TOML config layer for that role; relative paths resolve
  from the config file that declares the role." The scanner reads these tables from
  `$CODEX_HOME/config.toml` (default `~/.codex/config.toml`) and
  `./.codex/config.toml` and scans the declared files wherever they live. It reports
  a declared role under the table key. In the code (reported,
  `codex-rs/agent-roles/src/loader.rs` and `agent_role_config.rs`), the name comes
  from the file's `name` when it sets one and from the table key otherwise, the
  description from the file first and then the table, and a declared file may leave
  `developer_instructions` out (the child keeps the parent's) but not blank.
- Codex has no per-agent tool allowlist; the scanner raises no tool flags for Codex
  agents (see tool-catalog.md).

**Flags**
- `[high] CODEX_MISSING_REQUIRED` — a required key is missing or blank; Codex
  refuses the agent. For a declared role only the description and a blank
  `developer_instructions` count; a description that is blank in the file counts
  even when the table has one, because Codex rejects the blank before it falls back
  to the table (reported, `codex-rs/agent-roles/src/agent_role_config.rs`).
- `[high] CODEX_CLAUDE_KEY` — a Claude Code key (`tools`, `skills` or `hooks` as
  anything but a table, `disallowedTools`, `permissionMode`, `effort`, `color`, `memory`, `maxTurns`,
  `mcpServers`, `background`, `isolation`, `initialPrompt`). The role-file parser
  denies unknown fields, and Codex's own `tools`, `skills` and `hooks` are tables,
  so Codex skips the whole agent (reported,
  `codex-rs/agent-roles/src/agent_role_config.rs`). Remove them; Claude's `effort` is
  `model_reasoning_effort` here. A `[tools]`, `[[skills.config]]` or `[hooks]` table
  is Codex's own and is not flagged here.
- `[high] CODEX_UNKNOWN_KEY` — a top-level key that is neither a Codex key nor a
  Claude key (`prompt`, `version`). The known list is the role-file keys (`name`,
  `description`, `nickname_candidates`) plus every `ConfigToml` field at
  rust-v0.156.1 (reported, `codex-rs/config/src/config_toml.rs`); Codex skips an
  agent with a key it does not know. Fix a misspelling or move the content into
  `developer_instructions`.
- `[high] CODEX_CLAUDE_MODEL` — `model` is a Claude value (`sonnet`, `opus`,
  `haiku`, `fable`, `inherit`, or `claude-...`). `model` is a plain string, so
  Codex still loads the agent, but it cannot resolve the model and the agent's
  requests fail. A `claude-...` ID drops to `[med]` when the agent file or the
  config that declares it sets `model_provider`, which might serve it; the bare
  aliases stay `[high]`.
- `[med] CODEX_SUFFIX_CASE` — an undeclared file whose suffix is not lowercase
  `.toml` (`Agent.TOML`). Codex's discovery matches `toml` exactly (reported,
  `codex-rs/agent-roles/src/discovery.rs`), so it will not load the file from an
  agents folder. Rename it, or declare it with `[agents.<name>] config_file`.
- `[info] CODEX_DECLARED_NAME` — a declared role's file sets a `name` that differs
  from its table key. The code registers the role under the file's `name`
  (reported). The scanner keeps the table key and never proposes a rename; ask
  which name callers use.
- `[low] CODEX_IGNORED_KEY` — `sandbox_mode`, `approval_policy`, `mcp_servers`,
  `model_provider`, `notify`, `apps`, `hooks`, `service_tier`, `openai_base_url`,
  `chatgpt_base_url`. The docs say a file may include "other supported
  `config.toml` keys ... such as `model`, `model_reasoning_effort`, `sandbox_mode`,
  `mcp_servers`, and `skills.config`". The code since Codex 0.149 applies only
  `developer_instructions`, `model`, `model_reasoning_effort`,
  `model_reasoning_summary`, `model_verbosity`, `personality`, and disable-only
  `[features]` and `skills` entries; the other keys parse and are not applied
  (reported, `codex-rs/core/src/agent/role.rs`). `role.rs` also copies
  `service_tier`, but the spawn then replaces it with the parent's tier
  (`codex-rs/core/src/agent/child_config.rs`, `apply_spawn_agent_service_tier`; and
  `codex-rs/core/src/agent/control/spawn.rs` on resume), so it is inert too. On sandboxing the docs say
  "Subagents inherit your current sandbox policy." Older Codex still applies these
  keys, so keep them and report them as inert on 0.149 and later; never propose
  removing them.
- `[med] CODEX_EFFORT_INVALID` — outside `low`, `medium`, `high`, `xhigh`, `max`,
  `ultra` ("Reasoning effort advertised by the selected model, such as `low`,
  `medium`, `high`, `xhigh`, `max`, or `ultra`. Available levels depend on the model
  and client."). `minimal` and `none` exist in the code but no model in the bundled
  catalog offers them (reported, `codex-rs/models-manager/models.json`).
- `[med] CODEX_EFFORT_UNSUPPORTED` — the level is outside what the model offers,
  per the scanner's dated table. The docs say "GPT-6 Luna supports reasoning efforts
  up to **Max**, but not **Ultra**"; the other ranges, such as `gpt-5.6-luna` (up
  to `max`) and `gpt-5.5` (up to `xhigh`), come from the bundled model catalog
  (reported, `codex-rs/models-manager/models.json`). When a role changes the model
  or effort, the code checks the level against the model and fails the spawn with
  "Reasoning effort ... is not supported for model ..." (reported,
  `codex-rs/core/src/agent/child_config.rs`). Unknown models are not checked,
  because the live catalog is per account.
- `[med] CODEX_MODEL_RETIRED` — for ChatGPT sign-in: "On October 14, 2026, GPT-5.5
  will retire from ChatGPT, ChatGPT Work, and Codex on all plans"; "The `gpt-5.4`
  and `gpt-5.4-mini` models retired from Codex with ChatGPT sign-in on August 31,
  2026"; "The `gpt-5.2` and `gpt-5.3-codex` models are already deprecated in Codex
  when you sign in with ChatGPT." API-key use is not affected.
- `[low] CODEX_MODEL_WITHOUT_EFFORT` — "A custom agent file that sets only `model`
  preserves this previously resolved effort. Set `model_reasoning_effort` in the
  file too if the selected model doesn't support that effort or you want a
  different one."
- Shared with Claude agents: `LONG_DESCRIPTION`, `LONG_BODY` (on
  `developer_instructions`), `EMPHASIS_DENSITY`, `NO_OUTPUT_FORMAT` and duplicate
  blocks. `WEAK_TRIGGER` is not raised: Codex spawns agents "after a direct request
  or applicable project or skill instruction", not by matching the description.

**Model and effort**
- Resolution: "If you don't configure a subagent model or `model_reasoning_effort`,
  the subagent inherits the parent agent's model and reasoning effort." Values in
  the agent file take precedence. The default model depends on the account; don't
  name a fixed one.
- Models (subagents page): `gpt-6-sol` — "Start here for demanding agents. It's strongest for
  ambiguous, multi-step work that needs planning, tool use, validation, and
  follow-through across a larger context." `gpt-6-luna` — "Use for fast, narrowly
  scoped agents handling clear, repeatable, or high-volume work."
- Effort (subagents page): "start with `medium` for GPT-6 Sol, `high` for GPT-6
  Luna, or `low` for GPT-6 Astra. Adjust for the task using a level the selected
  model supports." `high`: "Use when an agent needs to trace complex logic, check
  assumptions, or work through edge cases (for example, reviewer or
  security-focused agents)." `low`: "Use when the task is straightforward and speed
  matters most." The page's examples run Luna at `high` (explorers, mappers,
  fixers) and Sol at `medium` (a reviewer, a debugger). The models page adds "Most
  tasks do not need Max or Ultra." and "Reasoning efforts don't map exactly between
  model generations"; they do not map to Claude's levels either.
- So: Sol at medium is the starting point for demanding agents, Luna for narrow,
  repeatable, high-volume work (at high in the docs' examples), and high effort for
  reviewer or security agents that trace complex logic, whatever the model.
- Fleet defaults: `[agents] default_subagent_model` ("Default model for spawned
  agents. An explicit spawn model takes precedence.") and
  `default_subagent_reasoning_effort` in `config.toml`, instead of pinning every file.
- As for Claude, any model or effort change is a candidate to verify on the agent's
  real task.

**Editing a Codex agent file**
- Change only the key lines you mean to change; never re-serialise the file (it
  loses comments and ordering). Keep top-level keys above the first `[table]`
  header, or TOML reads them as part of that table.
- `developer_instructions` stays a TOML string (a `"""` block is fine).
- Never add a key Codex does not know: that disables the agent. So no `version`
  field and no version bump; `bump_version.py` refuses `.toml` files. Adding
  `model_reasoning_effort` is fine. Never add or change `name` on a declared role.
- Leave `CODEX_IGNORED_KEY` keys in place; they still work on older Codex.
- The scanner does not follow symlinked agent files; that is its own safety rule.
  Codex does follow them (reported, `codex-rs/exec-server/src/local_file_system.rs`
  `read_directory`).

## Cross-cutting

- Scope: project agents (`.claude/agents/`) should be checked into VCS for the team;
  a user-global agent that hardcodes one project's paths is mis-scoped.
- `Task` is the old name of the `Agent` tool; rename when you touch the file.
- Precedence (high→low): managed → `--agents` CLI → project → user → plugin.

## Tensions / judgement calls

- Description length: detailed enough to trigger reliably vs. lean enough not to tax
  every session. Cap runaway multi-example blocks; don't strip a description down to
  a role line.
- The 55k/85% numbers are measured for MCP tool definitions through the API. Claude
  Code defers MCP tools by default and the docs do not say whether built-in schemas
  are deferred, so "omit `tools` → pays for every built-in schema" is directionally
  certain; treat the exact figure as MCP-derived and quote the scanner's own estimate.
- Conservative default: when unsure whether a tool is used, **flag it for the user**
  rather than removing it. Breaking an agent costs more than a slightly wide allowlist.
