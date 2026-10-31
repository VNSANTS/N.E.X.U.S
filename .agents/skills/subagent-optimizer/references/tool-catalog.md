# Tool catalogue & archetype → tools map

Claude Code only. Codex custom agents have no per-agent tool list: the only tool
controls in a Codex agent file are disable-only `[features]` switches (such as
`shell_tool`), as reported from the openai/codex source, and a Claude-style
`tools = [...]` key makes Codex skip the agent. Never propose an allowlist for a
Codex agent.

Use this to propose a minimal `tools` allowlist. Tool names vary slightly across
Claude Code versions — when a name in a file isn't here, treat it as possibly an
MCP tool (`mcp__*`), a plugin tool, or a newer/older built-in, and verify rather
than deleting it.

## Built-in tools

Names as documented at code.claude.com/docs/en/tools-reference (checked 2026-09).
Claude Code adds tools between releases; a name that is not here is not
automatically a typo.

**Read-only / safe** (no permission prompt; fine for any agent):
`Read`, `Grep`, `Glob`, `LSP`, `ToolSearch`, `ListMcpResourcesTool`, `ReadMcpResourceTool`

**Mutating / run code** (require permission; grant only if the agent's job needs them):
`Edit`, `Write`, `NotebookEdit`, `Bash`, `PowerShell`, `WebFetch`, `WebSearch`,
`Skill`, `Monitor`, `TaskStop`, `SendMessage`, `EnterWorktree`, `ExitWorktree`

**Task-list / coordination** (safe, but stripped from background subagents, see below):
`TaskCreate`, `TaskGet`, `TaskUpdate`, `TaskList`, `ListAgents`; `TodoWrite` (disabled by
default, kept for compatibility)

**Legacy names** you may still meet in older agent files (`LEGACY_TOOL_NAME`): `Task`
(now `Agent`), `LS` (use `Glob`/`Read`), `NotebookRead` (`Read`), `MultiEdit` (`Edit`),
`BashOutput` (`Monitor`), `KillShell` (`TaskStop`). Suggest the current name and flag;
verify against the installed version before deleting anything. (`TaskOutput` is
deprecated outright and sits on the blacklist below.)

**Never usable by a subagent — flag as dead entries in `tools`** (the documented
universal blacklist, `DEAD_TOOL_ENTRY`): `AskUserQuestion`, `EndConversation`,
`EnterPlanMode`, `ExitPlanMode` (unless `permissionMode: plan`), `ScheduleWakeup`,
`TaskOutput`, `WaitForMcpServers`, `Workflow`.

**`Agent` is conditional, not dead** (`NESTED_AGENT_TOOL`). Nested subagents are on by
default, up to three layers below the main conversation; at the depth limit, or with
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`, the harness withholds `Agent`. So a reviewer
that dispatches a verifier per finding legitimately lists `Agent`, and the docs' own
advice for keeping a subagent from spawning is to omit it. Treat it as a keep-or-drop
question: keep if the body delegates, drop if it never does.

**Background subagents lose some tools** (`BACKGROUND_STRIPPED`). Subagents run in the
background by default and then keep only `Read`, `Grep`, `Glob`, `Bash`, `PowerShell`,
`Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`, `TodoWrite`, `Skill`,
`ToolSearch`, `EnterWorktree`, `ExitWorktree`, `Monitor`, `TaskStop`, `SendMessage`,
`Artifact`. `TaskCreate`/`TaskGet`/`TaskUpdate`/`TaskList`, `ListAgents`, `LSP`,
`ListMcpResourcesTool` and `ReadMcpResourceTool` are removed whether inherited or
listed, so granting them only helps an agent launched in the foreground.

MCP tools are named `mcp__<server>__<tool>`. Claude Code defers MCP tool definitions
by default (only names and server instructions enter context until a tool is used),
but an unrestricted agent still inherits every built-in schema, which is the
avoidable cost.

## Archetype → minimal tool set

Match the agent's actual job (read the body), not its title. These are starting
points — widen only for a capability the body clearly exercises.

| Archetype | Tools | Notes |
|---|---|---|
| Read-only explorer / researcher | `Read, Grep, Glob` | + `WebFetch, WebSearch` only for external research; + `Bash` only for read-only git |
| Code reviewer / critic / analyzer | `Read, Grep, Glob, Bash` | Bash for `git diff`. **No** `Edit`/`Write` |
| Planner / architect | `Read, Grep, Glob` | + `Write` only if it persists a plan file; + `WebSearch/WebFetch` for research |
| Implementer / coder | `Read, Edit, Write, Grep, Glob, Bash` | + `NotebookEdit` only if it touches notebooks |
| Debugger / fixer | `Read, Edit, Bash, Grep, Glob` | reads + targeted edits + run repro |
| Test runner / author | `Bash, Read, Grep, Glob` | + `Edit, Write` only if it writes tests |
| Bash / git ops | `Bash, Read, Grep, Glob` | constrain destructive ops via permission rules / `PreToolUse` hook, not by widening tools |
| Data / SQL | `Bash, Read, Write` | matches official data-scientist example |

## `tools` vs `disallowedTools`

- Allowlist (`tools:`) — name only what's needed. Best for narrow agents.
- Denylist (`disallowedTools:`) — when intent is "everything except writes",
  e.g. `disallowedTools: Write, Edit, NotebookEdit`. Applied before `tools`; a
  tool in both is removed.

## Memory-enabled agents need write tools

If the frontmatter sets `memory:` (e.g. `memory: user`), the agent maintains its own
`MEMORY.md` / topic files; the docs say `Read`, `Write` and `Edit` are enabled
automatically for that. Whether an explicit `tools:` allowlist can still block them
is not documented, so keep `Edit` + `Write` listed on a memory-enabled agent — a
missing tool silently breaks memory upkeep. `NotebookEdit` is not needed for memory
(memory files are Markdown).

## The net check

The allowlist should match what the body instructs. Two failure modes to flag:
- **Granted but unused** — tool in `tools` the body never calls for → remove.
- **Instructed but missing** — body says "edit the file" but `Edit` isn't granted
  → the agent will fail at runtime → add it (or this reveals the body is wrong).
