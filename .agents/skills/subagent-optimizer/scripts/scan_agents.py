#!/usr/bin/env python3
"""Scan Claude Code subagents and Codex custom agents and report optimisation signals.

Deterministic pass that does the measuring so the skill can spend its reasoning
on judgement calls. Parses YAML-ish frontmatter (line based, tolerant of the
JSON-escaped multi-line `description` strings the agent-creator emits), counts
sizes, estimates tokens (~chars/4), and raises heuristic flags.

Usage:
    python scan_agents.py [PATH ...] [--json] [--body-lines N] [--desc-chars N]

PATH may be an agent .md or .toml file or a directory (searched recursively; a
.md file with frontmatter carrying `name` is a Claude Code subagent, a .toml file
with a top-level `name` or `developer_instructions` is a Codex custom agent, and
a missing required field is reported as a flag rather than silently dropping the
file). Symlinked files are never followed; they are listed as not scanned, as
are files over 1 MiB and files that cannot be read or parsed.
With no PATH, scans ~/.claude/agents, ./.claude/agents, $CODEX_HOME/agents
(default ~/.codex/agents) and ./.codex/agents, plus every role file declared as
an [agents.<name>] table with `config_file` in $CODEX_HOME/config.toml or
./.codex/config.toml. SKILL.md files are skipped when walking a directory (they
carry the same frontmatter but are skills). Codex files need Python 3.11+
(tomllib); on older Pythons they are listed as not scanned.

Exit code is always 0; this is a reporter, not a gate.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10: Codex files are listed as not scanned
    tomllib = None

# --- Tool classification (mirror of references/tool-catalog.md) --------------
# Tools a SUBAGENT can never use even if listed -> dead entries in `tools`.
# Documented "universal blacklist" for subagents (code.claude.com/docs/en/sub-agents).
# `ExitPlanMode` is usable only with `permissionMode: plan`. `Agent` is NOT here:
# nested subagents are on by default (up to three layers), so a delegating agent may
# legitimately list it; it is surfaced as a question instead (NESTED_AGENT_TOOL).
SUBAGENT_DEAD_TOOLS = {
    "AskUserQuestion", "EndConversation", "EnterPlanMode", "ExitPlanMode",
    "ScheduleWakeup", "TaskOutput", "WaitForMcpServers", "Workflow",
}
# Names from older Claude Code releases that no longer appear in the tools reference.
LEGACY_TOOL_NAMES = {
    "Task": "Agent", "LS": "Glob or Read", "NotebookRead": "Read",
    "MultiEdit": "Edit", "BashOutput": "Monitor", "KillShell": "TaskStop",
}
# Removed from background subagents (the default) whether inherited or listed.
BACKGROUND_STRIPPED_TOOLS = {
    "TaskCreate", "TaskGet", "TaskUpdate", "TaskList", "ListAgents", "LSP",
    "ListMcpResourcesTool", "ReadMcpResourceTool",
}
# File-writing tools (presence on an agent that declares it doesn't write is a smell).
WRITE_FILE_TOOLS = {"Edit", "Write", "NotebookEdit"}
# Any of these (or no `tools` field at all) means the agent can change things.
MUTATING_TOOLS = WRITE_FILE_TOOLS | {"Bash"}
# Documented `effort` values (code.claude.com/docs/en/sub-agents); which ones a
# given model accepts varies, so this is only the outer set.
EFFORT_LEVELS = {"low", "medium", "high", "xhigh", "max"}
TOP_EFFORT_LEVELS = {"xhigh", "max"}
# Claude Code's effort table leaves Haiku out ("Models not listed here do not
# support effort", code.claude.com/docs/en/model-config), so any model value
# containing this (the `haiku` alias or a full Haiku ID) gets no effort advice.
# `inherit` and other IDs are not resolved here and keep the ordinary checks.
EFFORT_UNSUPPORTED_MODEL_MARK = "haiku"
# An explicit "I don't write/edit/change code" statement in the BODY is a
# high-signal read-only mandate. Matching role words in the NAME instead caused
# false positives (e.g. "plan-driven-coder" matched "plan" yet genuinely codes),
# so we key off the body declaration.
NO_WRITE_DECL = re.compile(
    r"read[\s-]only"
    r"|\b(?:never|do not|does not|don'?t|doesn'?t|without)\b(?!\s+forget)"
    r"(?:\s+\w+){0,2}?\s+(?:writ|edit|modif|chang|implement)\w*"
    r"\s+(?:\w+\s+){0,2}?(?:code|files?|codebase|source|implementation|anything"
    r"|disk|repo(?:sitory)?|fixes)\b", re.I)
EMPHASIS = re.compile(r"\b(MUST|MUST NOT|NEVER|ALWAYS|DO NOT|CRITICAL|"
                      r"IMPORTANT|MANDATORY|REQUIRED)\b")

# --- Codex custom agents: keys, models and efforts, as of 2026-09-24 ----------
# Refresh from https://learn.chatgpt.com/docs/agent-configuration/subagents,
# https://learn.chatgpt.com/docs/models,
# https://learn.chatgpt.com/docs/config-file/config-reference and the bundled
# model catalog in github.com/openai/codex (release rust-v0.156.1). The live
# catalog is per account, so an unknown model is never flagged.
CODEX_AS_OF = "2026-09-24"
CODEX_REQUIRED_KEYS = ("name", "description", "developer_instructions")
# Claude Code frontmatter keys. Codex skips an agent whose file has a key it does
# not know, or a known key with a value of the wrong type. `tools` and `skills`
# only count in Claude's list form; Codex's own `[tools]` and
# `[[skills.config]]` parse to tables.
CODEX_CLAUDE_KEYS = {
    "tools": None, "disallowedTools": None, "permissionMode": None,
    "effort": "model_reasoning_effort", "color": None, "memory": None,
    "hooks": None, "maxTurns": None, "skills": None, "mcpServers": None,
    "background": None, "isolation": None, "initialPrompt": None,
}
# Codex keys too when the value is a table (ToolsToml, SkillsConfig, HooksToml);
# any other type fails Codex's parse and the file is skipped.
CODEX_TABLE_KEYS = {"tools", "skills", "hooks"}
# Every top-level key an agent file may carry at rust-v0.156.1: the role-file
# keys (codex-rs/agent-roles/src/agent_role_config.rs, RawAgentRoleFileToml, which
# denies unknown fields) plus every ConfigToml field it flattens in
# (https://github.com/openai/codex/blob/rust-v0.156.1/codex-rs/config/src/config_toml.rs).
CODEX_KNOWN_KEYS = frozenset("""
name description nickname_candidates
model review_model model_provider model_context_window model_auto_compact_token_limit
model_auto_compact_token_limit_scope model_post_turn_compact_threshold_percent
approval_policy approvals_reviewer auto_review browser_use computer_use
shell_environment_policy allow_login_shell sandbox_mode allow_symlinked_codex_home
sandbox_workspace_write default_permissions permissions notify instructions
developer_instructions include_permissions_instructions include_apps_instructions
include_collaboration_mode_instructions include_environment_context
model_instructions_file compact_prompt forced_chatgpt_workspace_id forced_login_method
cli_auth_credentials_store mcp_servers mcp_enterprise_managed_auth
mcp_oauth_credentials_store mcp_oauth_callback_port mcp_oauth_callback_url
mcp_optional_startup_grace_ms model_providers project_doc_max_bytes
project_doc_fallback_filenames tool_output_token_limit background_terminal_max_timeout
thread_unload_delay_secs js_repl_node_path js_repl_node_module_dirs profile profiles
history sqlite_home log_dir file_opener tui hide_agent_reasoning
show_raw_agent_reasoning model_reasoning_effort plan_mode_reasoning_effort
model_reasoning_summary model_verbosity model_catalog_json personality service_tier
chatgpt_base_url apps_mcp_product_sku responses_api_metadata orchestrator
openai_base_url audio experimental_realtime_ws_base_url
experimental_realtime_webrtc_call_base_url experimental_realtime_ws_model realtime
experimental_realtime_ws_backend_prompt experimental_realtime_ws_startup_context
experimental_realtime_start_instructions experimental_thread_store_endpoint
experimental_thread_store projects web_search tools tool_suggest agents goals
memories skills hooks plugins marketplaces features
suppress_unstable_features_warning ghost_snapshot project_root_markers
check_for_update_on_startup disable_paste_burst analytics feedback apps desktop otel
windows notice experimental_compact_prompt_file experimental_use_unified_exec_tool
oss_provider
""".split())
# Parsed, but not applied to a custom agent from Codex 0.149 (the child keeps the
# parent's live settings; codex-rs/core/src/agent/role.rs applies only
# developer_instructions, model, model_reasoning_effort, model_reasoning_summary,
# model_verbosity, personality and disable-only features/skills). role.rs also
# copies service_tier, but the spawn then overwrites it with the parent's tier
# (core/src/agent/child_config.rs apply_spawn_agent_service_tier, called from
# prepare_agent_spawn_config; core/src/agent/control/spawn.rs on resume).
# Older Codex still applies them, so they are reported, never removed.
CODEX_IGNORED_KEYS = ("sandbox_mode", "approval_policy", "mcp_servers", "model_provider",
                      "notify", "apps", "hooks", "service_tier", "openai_base_url",
                      "chatgpt_base_url")
# Claude Code model values; Codex resolves none of them.
CODEX_CLAUDE_MODEL_ALIASES = {"sonnet", "opus", "haiku", "fable", "inherit"}
CODEX_EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max", "ultra")
CODEX_EFFORT_NOT_OFFERED = {"minimal", "none"}  # in the enum, offered by no current model
_ALL = set(CODEX_EFFORT_LEVELS)
_UP_TO_MAX = _ALL - {"ultra"}
CODEX_MODEL_EFFORTS = {
    "gpt-6-astra": _ALL, "gpt-6-sol": _ALL, "gpt-6-luna": _UP_TO_MAX,
    "gpt-5.6-sol": _ALL, "gpt-5.6-terra": _ALL, "gpt-5.6-luna": _UP_TO_MAX,
    "gpt-5.5": {"low", "medium", "high", "xhigh"},
}
CODEX_RETIRED_MODELS = {
    "gpt-5.5": "retires 2026-10-14", "gpt-5.4": "retired 2026-08-31",
    "gpt-5.4-mini": "retired 2026-08-31", "gpt-5.2": "deprecated",
    "gpt-5.3-codex": "deprecated",
}

MAX_AGENT_FILE_BYTES = 1024 * 1024  # bigger files are listed as not scanned
CODEX_AGENT_MARKERS = ("name", "developer_instructions")  # top level only
NEEDS_TOMLLIB = ("not scanned: Codex files need Python 3.11+ (tomllib); run the scanner "
                 "with python3.12 or python3.11, or `uv run --python 3.12 "
                 "scripts/scan_agents.py`")

DEFAULT_BODY_LINES = 150   # official single-purpose examples run ~25-45 lines
DEFAULT_DESC_CHARS = 1200  # description loads session-wide for routing


def est_tokens(text: str) -> int:
    return round(len(text) / 4)


def _scalar(raw: str) -> str:
    """Decode a plain or quoted single-line YAML scalar (strip matching quotes)."""
    v = raw.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def _truthy(raw: str) -> bool:
    return _scalar(raw).lower() in {"true", "yes", "on", "1"}


def _split_tools(raw: str) -> list[str]:
    """Tokenize a `tools` value: comma/newline separated, `[...]` flow lists,
    quoted items, `- item` block lists and `# comments`. Parentheses protect
    their contents, so `Agent(worker, researcher)` and `Bash(git diff:*, git log:*)`
    stay one tool each (quotes inside them are kept verbatim); quotes at the top
    level are decoration and are dropped."""
    tokens: list[str] = []
    buf: list[str] = []
    depth = 0
    i, n = 0, len(raw)
    while i < n:
        ch = raw[i]
        if depth == 0 and ch in "\"'":
            pass  # top-level quoting is decoration
        elif ch == "#" and depth == 0 and (i == 0 or raw[i - 1] in " \t\n"):
            while i < n and raw[i] != "\n":
                i += 1
            continue
        elif ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(depth - 1, 0)
            buf.append(ch)
        elif depth == 0 and ch in ",\n[]":
            tokens.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    tokens.append("".join(buf))
    out = []
    for tok in tokens:
        tok = tok.strip()
        if tok.startswith("-"):
            tok = tok[1:].strip()
        if tok:
            out.append(tok)
    return out


def _base_name(tool: str) -> str:
    """`Agent(worker)` -> `Agent`; `mcp__x__y` unchanged."""
    return tool.split("(", 1)[0].strip()


def _memory_value(raw: str) -> str:
    """`memory: false/no/off/0` means disabled; return "" for those."""
    v = raw.strip().strip("\"'")
    return "" if v.lower() in {"", "false", "no", "off", "0", "none"} else v


class NotScanned(Exception):
    """A file that looks like an agent but could not be read as one."""


def _text(v) -> str:
    """A TOML value as display text: strings as-is, other types via str()."""
    return v if isinstance(v, str) else ("" if v is None else str(v))


def _table_with_instructions(data: dict, prefix: str = ""):
    """The first nested table holding `developer_instructions`, as (dotted
    header, table), or ("", None). Only that Codex-specific key counts: a table
    with just a `name` is ordinary TOML (pyproject's [project], Cargo's [package])."""
    for key, value in data.items():
        header = f"{prefix}.{key}" if prefix else key
        for table in (value if isinstance(value, list) else [value]):
            if isinstance(table, dict):
                if "developer_instructions" in table:
                    return header, table
                found = _table_with_instructions(table, header)
                if found[1] is not None:
                    return found
    return "", None


def parse_codex_agent(path: Path, declared: dict | None = None):
    """Parse a Codex custom agent (.toml) into the shared agent dict.

    `declared` is the config.toml declaration ({"role", "description",
    "config"}) when the file is a declared role's config_file: it is then always
    an agent, named after the table key, and may take its description from the
    table.

    Returns None for a .toml that is not an agent (no top-level name or
    developer_instructions, e.g. pyproject.toml). Raises NotScanned when the
    file cannot be read as TOML here, or when its agent keys sit inside a table."""
    if tomllib is None:
        raise NotScanned(NEEDS_TOMLLIB)
    try:
        raw = path.read_text(encoding="utf-8-sig")  # strict: Codex reads UTF-8 only
    except UnicodeDecodeError as exc:
        raise NotScanned(f"not scanned: not UTF-8 ({exc.reason} at byte {exc.start})") from exc
    try:
        data = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        raise NotScanned(f"not scanned: TOML parse error ({exc})") from exc
    except RecursionError as exc:
        raise NotScanned("not scanned: TOML nested too deeply to parse") from exc
    if declared is None and not any(k in data for k in CODEX_AGENT_MARKERS):
        header, table = _table_with_instructions(data)
        if table is not None:
            found = [f"`{k}`" for k in CODEX_AGENT_MARKERS if k in table]
            raise NotScanned(
                f"not scanned: {' and '.join(found)} {'sit' if len(found) > 1 else 'sits'} "
                f"below the [{header}] header, so {'they belong' if len(found) > 1 else 'it belongs'} "
                "to that table and Codex will not see an agent here. Move the agent keys "
                "above the first [table] header.")
        return None
    body = _text(data.get("developer_instructions")).strip("\n")
    desc = _text(data.get("description"))
    name = _text(data.get("name"))
    extra = {}
    if declared is not None:
        name = declared["role"]
        if not desc.strip():
            desc = declared.get("description") or ""
        extra["declared"] = {"role": declared["role"], "config": declared["config"]}
        extra["_config_provider"] = declared.get("provider", False)
    body_tokens = est_tokens(body)
    fm_tokens = max(est_tokens(raw) - body_tokens, 0)
    return {
        **extra,
        "path": str(path),
        "format": "codex",
        "name": name,
        "model": _text(data.get("model")),  # "" => parent's model (or [agents] default)
        "effort": _text(data.get("model_reasoning_effort")),
        "permission_mode": "",
        "omit_claude_md": False,
        "memory": "",
        "has_tools": False,  # Codex has no per-agent tool allowlist
        "tools": [],
        "description": desc,
        "desc_chars": len(desc),
        "desc_tokens": est_tokens(desc),
        "body": body,
        "body_lines": body.count("\n") + 1 if body else 0,
        "body_chars": len(body),
        "body_tokens": body_tokens,
        "frontmatter_tokens": fm_tokens,   # includes the description
        "total_tokens": fm_tokens + body_tokens,
        "_keys": data,
        "_paragraphs": [q.strip() for q in re.split(r"\n\s*\n", body)
                        if len(q.strip()) >= 120],
    }


def parse_agent(path: Path, declared: dict | None = None):
    """Return a dict of parsed fields, or None if the file isn't an agent."""
    if path.suffix.lower() == ".toml":
        return parse_codex_agent(path, declared)
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    if not raw.lstrip().startswith("---"):
        return None
    # Split frontmatter / body on the first two `---` fences.
    lines = raw.splitlines()
    start = next((i for i, l in enumerate(lines) if l.strip() == "---"), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].strip() == "---"), None)
    if end is None:
        return None
    fm_lines = lines[start + 1:end]
    body = "\n".join(lines[end + 1:]).strip("\n")

    # Line-based key parse: a new key matches `key:`; other lines continue the
    # previous value (covers block scalars + the escaped multi-line description).
    fields: dict[str, str] = {}
    cur = None
    key_re = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")
    for l in fm_lines:
        m = key_re.match(l)
        if m and not l.startswith((" ", "\t", "-")):
            cur = m.group(1)
            fields[cur] = m.group(2)
        elif cur is not None:
            fields[cur] += "\n" + l
    # `name` is the agent-specific marker. A file with `name` but no
    # `description` is a BROKEN agent (description is required) — surface it and
    # flag the gap rather than silently dropping it.
    if "name" not in fields:
        return None

    tools_raw = fields.get("tools")
    tools = _split_tools(tools_raw) if tools_raw is not None else []
    # An empty list (`tools: []`) is treated like a missing field: nothing is granted
    # explicitly, so the agent still inherits everything.
    has_tools = bool(tools)

    desc_raw = fields.get("description", "")
    desc = _scalar(desc_raw) if "\n" not in desc_raw else desc_raw
    return {
        "path": str(path),
        "format": "claude",
        "name": _scalar(fields.get("name", "")),
        "model": _scalar(fields.get("model", "")),  # "" => inherit (default)
        "effort": _scalar(fields.get("effort", "")),  # "" => inherits from session
        "permission_mode": _scalar(fields.get("permissionMode", "")),
        "omit_claude_md": _truthy(fields.get("omitClaudeMd", "")),
        "memory": _memory_value(fields.get("memory", "")),
        "has_tools": has_tools,
        "tools": tools,
        "description": desc,
        "desc_chars": len(desc),
        "desc_tokens": est_tokens(desc),
        "body": body,
        "body_lines": body.count("\n") + 1 if body else 0,
        "body_chars": len(body),
        "body_tokens": est_tokens(body),
        "frontmatter_tokens": est_tokens("\n".join(fm_lines)),   # includes the description
        "total_tokens": est_tokens("\n".join(fm_lines)) + est_tokens(body),
        "_paragraphs": [p.strip() for p in re.split(r"\n\s*\n", body)
                        if len(p.strip()) >= 120],
    }


def _long_description(a, add, desc_limit):
    if a["desc_chars"] > desc_limit:
        add("low", "LONG_DESCRIPTION",
            f"description is {a['desc_chars']} chars (~{a['desc_tokens']} tok); "
            "it loads session-wide for routing. Keep triggers + 1-2 tight examples.")


def _long_body(a, add, body_limit):
    if a["body_lines"] > body_limit:
        add("med", "LONG_BODY",
            f"body is {a['body_lines']} lines; single-purpose agents run "
            "~25-45. Check for redundancy / over-explaining.")


def _style_flags(a, add):
    emph = len(EMPHASIS.findall(a["body"]))
    if emph >= 12:
        add("low", "EMPHASIS_DENSITY",
            f"{emph} ALL-CAPS imperatives (MUST/NEVER/ALWAYS...). High density "
            "reads as nagging; explain the why instead.")
    if not re.search(r"(output format|return|report|summary|deliverable)",
                     a["body"], re.I):
        add("low", "NO_OUTPUT_FORMAT",
            "No explicit output-format / 'return a concise summary' section; "
            "agent may dump verbose output into the parent's context.")


def flag_codex_agent(a: dict, body_limit: int, desc_limit: int) -> list[dict]:
    """Codex custom agents: key, model and effort checks plus the shared
    description/body checks. No tool flags (Codex has no per-agent tool list)."""
    flags = []

    def add(sev, code, msg):
        flags.append({"severity": sev, "code": code, "message": msg})

    keys = a["_keys"]
    decl = a.get("declared")
    if decl is None:
        missing = [k for k in CODEX_REQUIRED_KEYS if not _text(keys.get(k)).strip()]
        why = "Codex refuses an agent without name, description and developer_instructions."
    else:
        # A declared role takes its name from the table key and may take its
        # description from the table; its file may leave developer_instructions
        # out (the child keeps the parent's), but not blank
        # (codex-rs/agent-roles/src/agent_role_config.rs at rust-v0.156.1).
        # A blank description in the file is an error before any table fallback
        # (normalize_agent_role_description), so it counts even with a table one.
        file_desc = keys.get("description")
        blank_in_file = file_desc is not None and not _text(file_desc).strip()
        missing = [] if a["description"].strip() and not blank_in_file else ["description"]
        if "developer_instructions" in keys and not _text(keys["developer_instructions"]).strip():
            missing.append("developer_instructions")
        why = ("Codex refuses a declared role with no description in the file or the "
               "table, or with a blank developer_instructions.")
    if missing:
        add("high", "CODEX_MISSING_REQUIRED", f"Missing or blank: {', '.join(missing)}. {why}")
    file_name = _text(keys.get("name")).strip()
    if decl is not None and file_name and file_name != decl["role"]:
        add("info", "CODEX_DECLARED_NAME",
            f"Declared as [agents.{decl['role']}] in {decl['config']}, but the file sets "
            f"name = '{file_name}'. Codex rust-v0.156.1 registers the role under the file's "
            "`name`. Reported under the table key; nothing is renamed. Check which name "
            "callers use.")
    claude = [k for k in CODEX_CLAUDE_KEYS if k in keys
              and not (k in CODEX_TABLE_KEYS and isinstance(keys[k], dict))]
    if claude:
        add("high", "CODEX_CLAUDE_KEY",
            "Claude Code keys in a Codex agent: " + "; ".join(
                k + (f" (Codex uses {CODEX_CLAUDE_KEYS[k]})" if CODEX_CLAUDE_KEYS[k] else "")
                for k in claude)
            + ". Codex rejects unknown keys and skips the whole agent. Remove them.")
    unknown = [k for k in keys if k not in CODEX_KNOWN_KEYS and k not in CODEX_CLAUDE_KEYS]
    if unknown:
        add("high", "CODEX_UNKNOWN_KEY",
            f"Keys Codex does not know: {', '.join(unknown)}. Codex skips an agent with a "
            f"key it does not know (known keys as of {CODEX_AS_OF}, Codex rust-v0.156.1). "
            "Fix a misspelling, or move the content into developer_instructions.")
    ignored = [k for k in CODEX_IGNORED_KEYS if k in keys
               and not (k in CODEX_TABLE_KEYS and not isinstance(keys[k], dict))]
    if ignored:
        add("low", "CODEX_IGNORED_KEY",
            f"{', '.join(ignored)}: not applied to custom agents from Codex 0.149 (the agent "
            "uses the parent's live settings); older Codex still applies it, so it stays. "
            "Don't rely on it on 0.149 and later.")

    model, effort = a["model"], a["effort"]
    if effort and effort not in CODEX_EFFORT_LEVELS:
        why = (" is not offered by current models" if effort in CODEX_EFFORT_NOT_OFFERED
               else " is not a documented level")
        add("med", "CODEX_EFFORT_INVALID",
            f"model_reasoning_effort '{effort}'{why}; use one of "
            f"{', '.join(CODEX_EFFORT_LEVELS)} that the model offers.")
    elif effort and model in CODEX_MODEL_EFFORTS and effort not in CODEX_MODEL_EFFORTS[model]:
        offered = [e for e in CODEX_EFFORT_LEVELS if e in CODEX_MODEL_EFFORTS[model]]
        add("med", "CODEX_EFFORT_UNSUPPORTED",
            f"{model} does not offer effort '{effort}' (offers {', '.join(offered)}, "
            f"as of {CODEX_AS_OF}); Codex rejects the combination.")
    if model.lower() in CODEX_CLAUDE_MODEL_ALIASES:
        add("high", "CODEX_CLAUDE_MODEL",
            f"model '{model}' is a Claude Code value; Codex cannot resolve it, so the agent "
            "loads but its requests fail. Pick a Codex model and a model_reasoning_effort "
            "it offers.")
    elif model.lower().startswith("claude-"):
        provider = bool(keys.get("model_provider")) or a.get("_config_provider", False)
        add("med" if provider else "high", "CODEX_CLAUDE_MODEL",
            f"model '{model}' is a Claude model ID; Codex cannot resolve it"
            + (" unless your model_provider serves it" if provider else "")
            + ", so the agent loads but its requests fail. Pick a Codex model and a "
            "model_reasoning_effort it offers.")
    if model in CODEX_RETIRED_MODELS:
        add("med", "CODEX_MODEL_RETIRED",
            f"{model} {CODEX_RETIRED_MODELS[model]} for ChatGPT sign-in, as of "
            f"{CODEX_AS_OF}. Pick an available model (and a level it offers).")
    if model and not effort:
        add("low", "CODEX_MODEL_WITHOUT_EFFORT",
            "`model` is set without `model_reasoning_effort`: the agent keeps the "
            "previously resolved effort, which this model may not offer. Set both.")

    suffix = Path(a["path"]).suffix
    if suffix != ".toml" and decl is None:
        stem = Path(a["path"]).stem
        add("med", "CODEX_SUFFIX_CASE",
            "Codex finds agents only in files ending in lowercase .toml (rust-v0.156.1, "
            "agent-roles/src/discovery.rs); it will not load this file from an agents "
            f"folder. Rename it to {stem}.toml, or declare it with [agents.<name>] "
            "config_file.")

    _long_description(a, add, desc_limit)
    _long_body(a, add, body_limit)
    _style_flags(a, add)
    return flags


def flag_agent(a: dict, body_limit: int, desc_limit: int) -> list[dict]:
    if a.get("format") == "codex":
        return flag_codex_agent(a, body_limit, desc_limit)
    flags = []

    def add(sev, code, msg):
        flags.append({"severity": sev, "code": code, "message": msg})

    if not a["has_tools"]:
        add("high", "NO_TOOLS_FIELD",
            "No `tools` field: inherits ALL tools every launch. Propose a "
            "minimal explicit allowlist (token + accuracy win).")
    else:
        bases = [_base_name(t) for t in a["tools"]]
        dead = [t for t in bases if t in SUBAGENT_DEAD_TOOLS
                and not (t == "ExitPlanMode" and a["permission_mode"] == "plan")]
        if dead:
            add("med", "DEAD_TOOL_ENTRY",
                f"Tools a subagent can never use: {', '.join(dead)}. Remove.")
        legacy = [t for t in bases if t in LEGACY_TOOL_NAMES]
        if legacy:
            add("med", "LEGACY_TOOL_NAME",
                "Names from older releases: " + "; ".join(
                    f"{t} -> {LEGACY_TOOL_NAMES[t]}" for t in legacy)
                + ". Rename (verify against the installed version first).")
        if "Agent" in bases:
            add("low", "NESTED_AGENT_TOOL",
                "Lists `Agent`: fine if the body delegates to sub-subagents (nesting is "
                "on by default, up to three layers); dead at the depth limit or with "
                "nesting off. Keep or drop? Ask, don't strip.")
        stripped = [t for t in bases if t in BACKGROUND_STRIPPED_TOOLS]
        if stripped:
            add("low", "BACKGROUND_STRIPPED",
                f"Removed from background subagents (the default): {', '.join(stripped)}. "
                "Keep only if the agent is launched in the foreground.")
        if len(a["tools"]) > 10:
            add("med", "MANY_TOOLS",
                f"{len(a['tools'])} tools listed; a single-purpose agent rarely needs more "
                "than ~10, and every extra schema costs tokens and selection accuracy. "
                "Trim to what the body actually uses.")
        # Read-only contradiction. A memory-enabled agent (memory: set) legitimately
        # needs Edit + Write to maintain its memory files, so those are justified
        # there and only the rest (e.g. NotebookEdit) is suspect.
        write_tools = [t for t in bases if t in WRITE_FILE_TOOLS]
        if write_tools and NO_WRITE_DECL.search(a["body"]):
            mem = bool(a["memory"])
            justified = {"Edit", "Write"} if mem else set()
            suspect = [t for t in write_tools if t not in justified]
            if suspect:
                extra = (f" (Edit/Write kept for memory upkeep; {', '.join(suspect)} "
                         "isn't needed for that)") if mem else ""
                add("med", "WRITE_ON_READONLY",
                    f"Body declares it doesn't write code, yet grants {', '.join(suspect)}. "
                    f"Drop unless it truly writes.{extra}")

    if a["omit_claude_md"]:
        add("info", "OMITS_CLAUDE_MD",
            "`omitClaudeMd: true`: this agent does NOT inherit CLAUDE.md, so rules "
            "written into its body may be the only copy. Do not trim them as duplicates.")

    if not a["model"]:
        add("low", "MODEL_INHERIT",
            "No `model`: defaults to `inherit` (uses parent's model). Pin "
            "haiku for mechanical/read-only, or sonnet/opus if competence is fixed.")

    if EFFORT_UNSUPPORTED_MODEL_MARK in a["model"].lower():
        if a["effort"]:
            add("low", "EFFORT_UNSUPPORTED",
                f"effort {a['effort']} on `{a['model']}`: the pinned model does not support "
                "effort, so the field does nothing while it runs the agent. A per-invocation "
                "model override can still run it on a model that does. A note, not a fix.")
    elif not a["effort"]:
        add("low", "EFFORT_INHERIT",
            "No `effort`: runs at the session's effort level. Pin it with the model "
            "when the job's depth is fixed (low for lookups, high for planners).")
    elif a["effort"] not in EFFORT_LEVELS:
        add("med", "EFFORT_INVALID",
            f"effort '{a['effort']}' is not one of low, medium, high, xhigh, max.")
    elif (a["effort"] in TOP_EFFORT_LEVELS and a["has_tools"]
          and not {_base_name(t) for t in a["tools"]} & MUTATING_TOOLS):
        add("low", "HIGH_EFFORT_READONLY",
            f"effort {a['effort']} on a read-only agent. Does the job need it? "
            "A lower level is a candidate to verify on its real task.")

    if not a["description"].strip():
        add("high", "MISSING_DESCRIPTION",
            "No `description` (a required field): the agent won't auto-delegate "
            "and may be ignored. Add trigger conditions + what it does.")
    else:
        _long_description(a, add, desc_limit)
        if not re.search(
                r"\b(use when|use this|after|whenever|proactive(?:ly)?|immediately)\b",
                a["description"], re.I):
            add("med", "WEAK_TRIGGER",
                "description lacks explicit trigger conditions ('use when...', "
                "'after...', 'proactively'); may under-trigger.")

    _long_body(a, add, body_limit)
    if re.search(r"(persistent agent memory|## MEMORY\.md|your MEMORY\.md)",
                 a["body"], re.I):
        sev = "med" if a["memory"] else "low"
        add(sev, "MEMORY_BOILERPLATE",
            "Body hand-writes a persistent-memory section. With `memory:` set "
            "the harness already injects memory instructions + MEMORY.md; trim "
            "to a one-line 'update your memory as you learn'.")

    _style_flags(a, add)

    if a["name"] and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a["name"]):
        add("med", "NAME_FORMAT",
            f"name '{a['name']}' isn't lowercase-hyphenated.")
    return flags


def find_duplicate_blocks(agents: list[dict]) -> list[dict]:
    """Paragraphs (>=120 chars) appearing verbatim in >=2 agent files.

    Agents are keyed by file path, so two files that share a `name` (a Claude
    agent and its Codex port, or user and project copies) stay apart."""
    seen: dict[str, dict[str, str]] = {}
    for a in agents:
        for p in set(a["_paragraphs"]):
            norm = re.sub(r"\s+", " ", p).strip()
            seen.setdefault(norm, {})[a["path"]] = a["name"]
    dups = []
    for text, by_path in seen.items():
        if len(by_path) >= 2:
            files = sorted(by_path)
            dups.append({"chars": len(text), "tokens": est_tokens(text),
                         "agents": [by_path[f] for f in files], "files": files,
                         "preview": text[:90] + ("..." if len(text) > 90 else "")})
    dups.sort(key=lambda d: d["chars"] * len(d["files"]), reverse=True)
    return dups[:15]


def _is_candidate(path: Path) -> bool:
    return path.suffix == ".md" or path.suffix.lower() == ".toml"


def _symlink_note(path: Path) -> dict:
    return {"path": str(path),
            "reason": "not scanned: symlink (the scanner does not follow symlinks, which can "
                      "point outside the scanned folder)"}


def gather(paths: list[str], notes: list | None = None) -> list[Path]:
    """Agent candidates under `paths`. Symlinked files are never followed,
    whether named as an argument or met in a directory walk; when `notes` is
    given, each one is recorded there."""
    out: list[Path] = []

    def skip_link(f: Path) -> None:
        if notes is not None:
            notes.append(_symlink_note(f))

    for p in paths:
        pth = Path(p).expanduser()
        if pth.is_symlink() and _is_candidate(pth):
            skip_link(pth)
        elif pth.is_file() and _is_candidate(pth):
            out.append(pth)
        elif pth.is_dir():
            # SKILL.md also carries `name` + `description` frontmatter but is a
            # skill, not an agent; a directory walk must not audit it as one.
            # Nor is Codex's config.toml, whose [profiles.*] may hold
            # developer_instructions.
            for f in sorted(pth.rglob("*")):
                # config.toml is read only as the source of declared roles.
                if not _is_candidate(f) or f.name in ("SKILL.md", "config.toml"):
                    continue
                if f.is_symlink():
                    skip_link(f)
                elif f.is_file():
                    out.append(f)
    # de-dup (by real folder, so a declared role met again in a walk counts once), preserve order
    seen, uniq = set(), []
    for f in out:
        key = _file_key(f)
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq


def codex_home() -> Path:
    """$CODEX_HOME, else ~/.codex (as Codex resolves it)."""
    return Path(os.environ.get("CODEX_HOME") or "~/.codex").expanduser()


def codex_config_files() -> list[Path]:
    """Config files whose [agents.<name>] tables can declare roles."""
    return [codex_home() / "config.toml", Path.cwd() / ".codex" / "config.toml"]


def _file_key(path: Path) -> Path:
    """Compare paths by their real folder but keep the file itself unresolved,
    so a symlinked file is still seen as a symlink."""
    path = Path(os.path.abspath(path))
    return path.parent.resolve() / path.name


def declared_roles(config_files: list[Path], notes: list) -> dict[Path, dict]:
    """Role files declared as [agents.<name>] tables with a config_file, keyed by
    _file_key(path). A relative config_file resolves against the folder of the
    config.toml that declares it; a later config file wins for the same path."""
    roles: dict[Path, dict] = {}
    for cfg in config_files:
        cfg = Path(os.path.normpath(cfg))
        if not cfg.is_file():
            continue
        if tomllib is None:
            notes.append({"path": str(cfg), "reason": NEEDS_TOMLLIB})
            continue
        try:
            data = tomllib.loads(cfg.read_text(encoding="utf-8-sig"))
        except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError, RecursionError) as exc:
            notes.append({"path": str(cfg),
                          "reason": f"declared roles not read: {type(exc).__name__} ({exc})"})
            continue
        agents = data.get("agents")
        if not isinstance(agents, dict):
            continue
        for role, table in agents.items():
            if not isinstance(table, dict) or not isinstance(table.get("config_file"), str):
                continue  # a fleet setting, or a role with no file of its own
            target = Path(table["config_file"]).expanduser()
            if not target.is_absolute():
                target = cfg.parent / target
            desc = table.get("description")
            roles[_file_key(target)] = {
                "role": role, "config": str(cfg), "path": Path(os.path.normpath(target)),
                "provider": bool(data.get("model_provider")),
                "description": desc if isinstance(desc, str) and desc.strip() else None}
    return roles


def default_targets() -> list[str]:
    home, cwd = Path.home(), Path.cwd()
    return [str(home / ".claude/agents"), str(cwd / ".claude/agents"),
            str(codex_home() / "agents"), str(cwd / ".codex/agents")]


def scan_paths(paths: list[str], body_limit: int = DEFAULT_BODY_LINES,
               desc_limit: int = DEFAULT_DESC_CHARS, config_files: list | tuple = (),
               include_declared: bool = False) -> tuple[list[dict], list[dict]]:
    """Parse and flag every agent under `paths`; return (agents, skipped).

    Roles declared in `config_files` are recognised wherever the scan meets
    their file; with `include_declared` their files are scanned too, even
    outside an agents/ folder."""
    skipped: list[dict] = []
    agents = []
    declared = declared_roles(list(config_files), skipped)
    targets = [str(p) for p in paths]
    if include_declared:
        for d in declared.values():
            if d["path"].is_file() or d["path"].is_symlink():
                targets.append(str(d["path"]))
            else:
                skipped.append({"path": str(d["path"]),
                                "reason": f"not scanned: declared as [agents.{d['role']}] in "
                                          f"{d['config']}, but the file does not exist"})
    for f in gather(targets, skipped):
        try:
            if f.stat().st_size > MAX_AGENT_FILE_BYTES:
                raise NotScanned("not scanned: larger than 1 MiB")
            parsed = parse_agent(f, declared.get(_file_key(f)))
        except NotScanned as exc:
            skipped.append({"path": str(f), "reason": str(exc)})
            continue
        except (OSError, UnicodeDecodeError, RecursionError, ValueError) as exc:
            skipped.append({"path": str(f),
                            "reason": f"not scanned: {type(exc).__name__} ({exc})"})
            continue
        if parsed:
            parsed["flags"] = flag_agent(parsed, body_limit, desc_limit)
            agents.append(parsed)
    return agents, skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", help="agent .md files or directories")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--body-lines", type=int, default=DEFAULT_BODY_LINES)
    ap.add_argument("--desc-chars", type=int, default=DEFAULT_DESC_CHARS)
    args = ap.parse_args()

    paths = args.paths or default_targets()
    agents, skipped = scan_paths(paths, args.body_lines, args.desc_chars,
                                 config_files=codex_config_files(),
                                 include_declared=not args.paths)

    dups = find_duplicate_blocks(agents)

    if args.json:
        for a in agents:
            a.pop("body", None)
            a.pop("_paragraphs", None)
            a.pop("_keys", None)
            a.pop("_config_provider", None)
        print(json.dumps({"agents": agents, "duplicate_blocks": dups,
                          "count": len(agents), "skipped": skipped,
                          "metric": "definition text, chars/4; tool schemas and "
                                    "inherited context are not measured"}, indent=2))
        return

    if not agents:
        print("No agent files found in:", ", ".join(paths))
        _print_skipped(skipped)
        return

    sev_order = {"high": 0, "med": 1, "low": 2, "info": 3}
    print(f"Scanned {len(agents)} agent(s); token figures are definition text only\n" + "=" * 60)
    for a in agents:
        if a["format"] == "codex":
            tools = "Codex agent (no per-agent tool list)"
            model = a["model"] or "inherit (parent)"
            effort = a["effort"] or "inherit (parent)"
        else:
            tools = (f"{len(a['tools'])} tools" if a["has_tools"]
                     else "NO tools field (inherits all)")
            model = a["model"] or "inherit (default)"
            effort = a["effort"] or "inherit (session)"
        print(f"\n● {a['name']}  [{model}, effort {effort}]  {tools}")
        print(f"  {a['path']}")
        if a.get("declared"):
            print(f"  declared as [agents.{a['declared']['role']}] in {a['declared']['config']}")
        print(f"  definition text: desc ~{a['desc_tokens']} tok | body {a['body_lines']} lines "
              f"~{a['body_tokens']} tok | total ~{a['total_tokens']} tok "
              "(chars/4 of the file; tool schemas and inherited context not counted)")
        for fl in sorted(a["flags"], key=lambda f: sev_order[f["severity"]]):
            print(f"    [{fl['severity']:>4}] {fl['code']}: {fl['message']}")
        if not a["flags"]:
            print("    (no flags)")

    if dups:
        print("\n" + "=" * 60 + "\nDUPLICATED BLOCKS (shared verbatim across agents)")
        for d in dups:
            # Paths only where a name repeats, so the usual line stays short.
            where = ", ".join(f"{n} ({f})" if d["agents"].count(n) > 1 else n
                              for n, f in zip(d["agents"], d["files"]))
            print(f"  ~{d['tokens']} tok x{len(d['files'])} [{where}]: {d['preview']}")
        waste = sum(d["tokens"] * (len(d["files"]) - 1) for d in dups)
        print(f"  → ~{waste} tokens of repeated boilerplate across the set.")
    _print_skipped(skipped)


def _print_skipped(skipped: list[dict]) -> None:
    if skipped:
        print("\n" + "=" * 60 + "\nNOT SCANNED")
        for n in skipped:
            print(f"  {n['path']}: {n['reason']}")


if __name__ == "__main__":
    main()
