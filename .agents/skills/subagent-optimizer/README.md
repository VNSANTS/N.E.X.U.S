# subagent-optimizer: cut the token cost of Claude Code subagents and Codex agents

A subagent optimizer for Claude Code and OpenAI Codex, packaged as an agent skill. It reads your agent definition files, reports what each one wastes or gets wrong, and applies only the fixes you approve. It works on agent definitions only; for agent skills (`SKILL.md` folders) use `skill-optimizer`. It is plain Markdown plus two Python scripts, so it runs under Claude Code, Codex and anything else that loads `SKILL.md`.

- Claude Code subagents: `~/.claude/agents/*.md` and a project's `.claude/agents/`.
- Codex custom agents: `~/.codex/agents/*.toml` (or `$CODEX_HOME/agents/`), a project's `.codex/agents/`, and any role file that an `[agents.<name>]` table in `config.toml` points to with `config_file`. Reading them needs Python 3.11 or later.

Triggers: "audit my subagents", "optimize my agents", "audit my codex agents", "my agent uses too many tokens", "fix my agent's tools list", "review .claude/agents", "review .codex/agents", "make my agents cheaper".

## Why this exists

Claude Code already tells you how to write a subagent. It does not tell you what one costs. A subagent that omits the `tools` field inherits every tool, and every tool schema is sent on every single launch; agent prompts quietly accumulate boilerplate the harness already injects; a description that never says "use when" fails to trigger at all. None of that shows up in a diff, and `/doctor` covers skills and MCP servers, not agents.

Measured on Claude Code 2.1.278, the same one-line agent cost 18,437 input tokens on Haiku 4.5 with no `tools` field and 10,241 with `Read, Grep, Glob`. On Sonnet 5: 31,882 against 13,401.

## What it checks

| Flag | What it means | Typical fix |
|---|---|---|
| `NO_TOOLS_FIELD` | No `tools` field, so the agent inherits every tool on each launch | The minimal allowlist its body actually uses |
| `WRITE_ON_READONLY` | Body says it never edits code, yet `Edit`/`Write` are granted | Drop them, unless `memory:` is set and needs them |
| `DEAD_TOOL_ENTRY` | Tools a subagent can never use (`AskUserQuestion`, `Workflow`, `EndConversation`, plan and schedule tools) | Remove |
| `LEGACY_TOOL_NAME` | A name from an older release (`Task`, `LS`, `MultiEdit`) | Rename to the current tool |
| `NESTED_AGENT_TOOL` | Lists `Agent`; legitimate only if the body delegates | Asked as a question, never stripped silently |
| `BACKGROUND_STRIPPED` | Tools the harness removes from background subagents | Keep only for a foreground agent |
| `MANY_TOOLS` | More than ten tools on a single-purpose agent | Trim to what the body uses |
| `MEMORY_BOILERPLATE` | A hand-written memory section the harness already injects | One line |
| `WEAK_TRIGGER` | Description without "use when", "after" or a proactive cue | Concrete trigger conditions |
| `LONG_BODY`, `LONG_DESCRIPTION` | Prompt or routing description past the useful size | Cut duplication, keep one worked example |
| `MODEL_INHERIT` | No `model`, so it runs on whatever the session uses | Pin when competence is fixed, together with effort |
| `EFFORT_INHERIT` | No `effort`, so it reasons at the session's effort level | Pin with the model when the job's depth is fixed |
| `EFFORT_INVALID` | An `effort` value other than `low`, `medium`, `high`, `xhigh`, `max` | Use one of the five |
| `EFFORT_UNSUPPORTED` | `effort` set on a Haiku model; the pinned model does not support effort | A note only: a per-invocation model override can still run the agent on a model that does |
| `HIGH_EFFORT_READONLY` | `xhigh` or `max` on an agent that cannot edit files or run shell commands | Asked as a question; a lower level is a candidate to test on the agent's real task |
| `OMITS_CLAUDE_MD` | `omitClaudeMd: true`, so body rules may be the only copy | Never trimmed as duplicates |

Codex custom agents have no per-agent tool list, so none of the tool flags apply to them. They get their own checks, plus the length and duplicate-block checks above:

| Flag | What it means | Typical fix |
|---|---|---|
| `CODEX_MISSING_REQUIRED` | `name`, `description` or `developer_instructions` is missing or blank, so Codex refuses the agent | Fill it in |
| `CODEX_CLAUDE_KEY` | A Claude Code key such as a `tools` list or `effort`; Codex skips the whole agent | Remove it (`effort` becomes `model_reasoning_effort`) |
| `CODEX_UNKNOWN_KEY` | A top-level key that is neither a Codex key nor a Claude key, such as `prompt` or `version`; Codex skips the agent | Fix the spelling, or move the text into `developer_instructions` |
| `CODEX_CLAUDE_MODEL` | `model` is a Claude value (`sonnet`, `opus`, `haiku`, `fable`, `inherit`, `claude-...`). The agent loads, but Codex cannot resolve the model, so its requests fail (medium for a `claude-` ID when a `model_provider` is set) | A Codex model with a level it offers |
| `CODEX_SUFFIX_CASE` | A file ending in `.TOML` or another case other than lowercase `.toml`, which Codex will not load from an agents folder | Rename it to `.toml`, or declare it in `config.toml` |
| `CODEX_IGNORED_KEY` | `sandbox_mode`, `approval_policy`, `mcp_servers`, `hooks`, `service_tier` and similar keys, which Codex 0.149 and later do not apply to a custom agent | Kept: older Codex still applies them; reported as inert on 0.149+ |
| `CODEX_DECLARED_NAME` | A role declared in `config.toml` whose file sets a different `name` | A note; nothing is renamed |
| `CODEX_EFFORT_INVALID` | A `model_reasoning_effort` outside `low`, `medium`, `high`, `xhigh`, `max`, `ultra` | Use a level the model offers |
| `CODEX_EFFORT_UNSUPPORTED` | A level the pinned model does not offer, such as `ultra` on `gpt-6-luna` | A lower level, as a candidate to test |
| `CODEX_MODEL_RETIRED` | A model retired or deprecated for ChatGPT sign-in, such as `gpt-5.5` or `gpt-5.4` | An available model |
| `CODEX_MODEL_WITHOUT_EFFORT` | `model` set without `model_reasoning_effort`, so the agent keeps an effort the model may not offer | Set both |

The model, effort and key tables in the scanner are dated (2026-09-24, Codex rust-v0.156.1); your account's live model list is what counts, so unknown models are never flagged. Effort names do not map across model generations, or between Claude and Codex, so the skill never translates a level from one to the other.

## What it does not do

It does not write agents for you, invent tools an agent never mentions, or touch a file before you approve the report. It does not measure launch cost: the scanner counts the text of the agent file, and the tool-schema saving is reported as a policy change, not a number. For Codex agents it never adds a key Codex does not know, including a version field, because Codex skips an agent with such a key (it may add `model_reasoning_effort`, which Codex knows). It never removes keys that older Codex still applies, never adds or changes `name` on a role declared in `config.toml`, edits only the lines it changes and never rewrites the whole file.

## One real before and after

`bash-git-ops`, a real agent of mine, audited and edited by the skill. Frontmatter first:

```diff
 name: bash-git-ops
+version: 1.1.0
-description: "...four worked examples, 1,900 characters..."
+description: "...one worked example, 900 characters..."
+tools: Bash, Read, Grep, Glob, Edit, Write
 model: haiku
 memory: user
```

Then the body: a 46-line "Persistent Agent Memory" section, which the harness injects anyway for a `memory:` agent, became one line that keeps the part the harness does not say.

```diff
-# Persistent Agent Memory
-
-You have a persistent Persistent Agent Memory directory at `~/.claude/agent-memory/bash-git-ops/`.
-... 43 more lines ...
+Consult your agent memory before starting and update it as you learn; session
+transcripts are a slow last resort for past context.
```

145 lines became 102. `Edit` and `Write` stayed, because `memory: user` needs them and stripping them silently breaks memory upkeep. Launched on the same task, before and after, the agent returned the same answer and its first request went from 20,122 to 13,962 input tokens.

![Claude Code subagent launch tokens before and after subagent-optimizer, measured on Claude Code 2.1.278: a no-tools-field agent against a three-tool allowlist on Haiku and Sonnet, and three real agents that dropped 31%, 13% and 3% with equivalent results](<https://raw.githubusercontent.com/IonDen/skills/main/docs/images/subagent-optimizer-workflow.svg>)

Full method, table and harness: [`evals/subagent-optimizer/recorded/2026-09-19-launch-cost/`](<https://github.com/IonDen/skills/tree/main/evals/subagent-optimizer/recorded/2026-09-19-launch-cost/>).

## Install

```bash
npx skills add IonDen/skills --skill subagent-optimizer -g -a claude-code -y
npx skills add IonDen/skills --skill subagent-optimizer -g -a codex -y   # --copy for real files
```

The `-a claude-code` matters: most agents share `.agents/skills` and the CLI installs there by default, while Claude Code reads `.claude/skills` and is not pre-selected in the interactive picker.

As a plugin, which also keeps it updated:

```text
/plugin marketplace add IonDen/skills        # Claude Code
codex plugin marketplace add IonDen/skills   # Codex
```

By hand: copy this folder into `~/.claude/skills/` or `~/.agents/skills/`.

## Use

- "Audit my subagents": scans `~/.claude/agents/` and `~/.codex/agents/` and reports per agent.
- "Audit my Codex agents": the Codex files only.
- "Optimize the solution-architect agent": one agent.
- "Make the agents in .claude/agents cheaper": a project directory.

It reports first and stops. Nothing is edited until you say so.

## What ships

```text
subagent-optimizer/
├── SKILL.md                     the workflow: scope, scan, analyse, report, apply
├── agents/openai.yaml           Codex and ChatGPT metadata
├── references/
│   ├── best-practices.md        what each flag means and why
│   └── tool-catalog.md          built-in tools, the subagent blacklist, archetype to tools
└── scripts/
    ├── scan_agents.py           the scanner: flags, sizes, cross-agent duplicate blocks
    └── bump_version.py          bumps the version of an edited Claude agent (refuses Codex files)
```

The evals are in the repository under [`evals/subagent-optimizer/`](<https://github.com/IonDen/skills/tree/main/evals/subagent-optimizer/>): six prompts with expected outcomes, the agent fixtures they run against, and the measured runs with their harness. They don't install with the skill.

## Sources

The flag list follows Anthropic's own documentation: [subagents](<https://code.claude.com/docs/en/sub-agents>) for the frontmatter fields, the tool blacklist and nested-subagent rules, [tools reference](<https://code.claude.com/docs/en/tools-reference>) for current tool names, [costs](<https://code.claude.com/docs/en/costs>) for what is deferred, and the API [tool-search documentation](<https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool>) for the 55k-token and 85% figures, which were measured for MCP tool definitions.

## Version history

<details>
<summary>Show release notes</summary>

**1.4.1**: `scan_agents.py --json` gives each agent a `total_tokens` field (frontmatter plus body), the same total the readable output prints. The description's `desc_tokens` is already inside `frontmatter_tokens`, and adding all three overstated every agent; SKILL.md now says so and the report takes its figure from `total_tokens`.

**1.4.0**: The model advice now covers reasoning effort too. The scanner reads the `effort` field, prints it next to the model, and raises four new flags: `EFFORT_INHERIT` when the field is missing (not on Haiku, which has no effort levels), `EFFORT_UNSUPPORTED` when it is set on a Haiku model, `EFFORT_INVALID` for a value outside the five documented levels, and `HIGH_EFFORT_READONLY` when a read-only agent runs at `xhigh` or `max`. The skill recommends model and effort together from the agent's job and presents any change as a candidate to test. It also audits Codex custom agents (`.codex/agents/*.toml`, and roles declared in `config.toml`): `CODEX_*` flags cover missing required keys, Claude keys and unknown keys that make Codex skip the agent, Claude model values Codex cannot resolve, file names Codex will not load, keys newer Codex ignores (kept, because older versions apply them), effort levels the model does not offer, retired models and a model pinned without an effort. Duplicate blocks are now matched by file, so two agents with the same name stay apart. `bump_version.py` refuses Codex files. The description now says the skill is for agent definitions in both tools and that agent skills belong to `skill-optimizer`.

**1.3.1**: Two sentences in SKILL.md that only restated the sentence before them are gone. Behaviour is unchanged.

**1.3.0**: Renamed from `agent-optimiser` to `subagent-optimizer`, the words people search with. The old name is not kept as an alias.

**1.2.1**: Added US-spelling triggers ("optimize my subagents", "subagent optimizer") so the skill loads when people ask in those words. No change to the flags or the scripts.

**1.2.0**: First public release. Compared with the private version: `ExitPlanMode` is kept when the agent sets `permissionMode: plan`; parameterised tools such as `Agent(worker, researcher)` stay one tool; `omitClaudeMd: true` is surfaced so inlined rules are not trimmed as duplicates; the scanner labels its figures as definition text instead of launch cost; model changes are candidates to verify rather than savings. `bump_version.py` preserves quotes and line endings, refuses symlinks and writes atomically.

</details>

## Author and license

By [Denis Ineshin](<https://github.com/IonDen>). MIT.
