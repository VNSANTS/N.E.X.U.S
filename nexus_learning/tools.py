"""Typed allowlisted read tools; no arbitrary shell or filesystem execution."""
from dataclasses import dataclass
import json
import math
import re
import time

from .policy import PolicyEngine, READ, SENSITIVE, WRITE_REVERSIBLE
from .engine import now, uid


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    risk: str
    parameters: dict
    handler: object
    permission: str = None


class ToolRegistry:
    def __init__(self, engine):
        self.engine = engine
        with engine.db() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS api_activity(
              id TEXT PRIMARY KEY,user_id TEXT NOT NULL,event TEXT NOT NULL,
              details TEXT NOT NULL,created_at TEXT NOT NULL)""")
        self._tools = {
            "memory.search": ToolSpec(
                "memory.search", "Search active personal memories.", READ,
                {"query": str}, self._memory_search),
            "knowledge.claims": ToolSpec(
                "knowledge.claims", "List reviewed knowledge claims.", READ,
                {"state": str}, self._claims),
        }
        self.policy = PolicyEngine(allowed_tools=self._tools)

    def register(self, spec):
        """Register code-owned tools; model output cannot extend this registry."""
        if not isinstance(spec, ToolSpec) or not re.fullmatch(r"[a-z][a-z0-9_.-]{1,80}", spec.name or ""):
            raise ValueError("invalid tool specification")
        permission = spec.permission or spec.risk
        if spec.risk not in {READ, WRITE_REVERSIBLE, SENSITIVE} or permission != spec.risk:
            raise ValueError("invalid tool permission")
        if (not isinstance(spec.description, str) or len(spec.description) > 500
                or not isinstance(spec.parameters, dict)
                or any(not isinstance(key, str) or not isinstance(value, type)
                       for key, value in spec.parameters.items())
                or not callable(spec.handler)):
            raise ValueError("invalid tool specification")
        if spec.name in self._tools:
            raise ValueError("tool is already registered")
        self._tools[spec.name] = spec
        self.policy = PolicyEngine(allowed_tools=self._tools)
        return spec.name

    def list(self):
        return [{"id": x.name, "description": x.description, "risk": x.risk,
                 "parameters": {k: v.__name__ for k, v in x.parameters.items()}}
                for x in self._tools.values()]

    def model_tools(self):
        """OpenAI-compatible function declarations for explicitly allowlisted READ tools only."""
        types = {str: "string", int: "integer", float: "number", bool: "boolean",
                 dict: "object", list: "array"}
        result = []
        for spec in self._tools.values():
            if (spec.permission or spec.risk) != READ:
                continue
            properties = {}
            for name, value_type in spec.parameters.items():
                if value_type not in types:
                    raise ValueError("tool parameter type has no JSON Schema mapping")
                properties[name] = {"type": types[value_type]}
            result.append({"type": "function", "function": {
                "name": spec.name, "description": spec.description,
                "parameters": {"type": "object", "properties": properties,
                               "required": list(spec.parameters), "additionalProperties": False}}})
        return result

    def execute(self, name, arguments, *, owner_id, approved=False, context=None):
        spec = self._tools.get(name)
        permission = (spec.permission or spec.risk) if spec else READ
        decision = self.policy.evaluate(name, permission, approved)
        if not decision.allowed:
            self._audit(owner_id, "tool.denied", name, {
                "permission": permission,
                "risk": spec.risk if spec else "unknown",
                "decision": "denied",
                "reason_code": "approval_required" if decision.requires_approval else "not_allowlisted",
            })
            raise PermissionError(decision.reason)
        if spec is None:
            raise KeyError("unknown tool")

        started = time.monotonic()

        def elapsed_ms():
            return max(0, min(1_000_000_000, int((time.monotonic() - started) * 1000)))

        def audit_failed(error_type):
            self._audit(owner_id, "tool.failed", name, {
                "permission": permission, "risk": spec.risk,
                "decision": "allowed", "error_type": error_type[:64],
                "duration_ms": elapsed_ms(),
            })

        audit_context = {"permission": permission, "risk": spec.risk, "decision": "allowed"}
        self._audit(owner_id, "tool.started", name, audit_context)
        if not isinstance(arguments, dict) or set(arguments) != set(spec.parameters):
            audit_failed("invalid_arguments")
            raise ValueError("tool arguments do not match its schema")
        try:
            if len(json.dumps(arguments, ensure_ascii=False, allow_nan=False).encode("utf-8")) > 8000:
                raise ValueError("tool arguments exceed configured limit")
        except (TypeError, ValueError):
            audit_failed("invalid_arguments")
            raise ValueError("tool arguments are not valid bounded JSON") from None
        for key, expected in spec.parameters.items():
            value = arguments[key]
            invalid = not isinstance(value, expected)
            if expected is int and isinstance(value, bool):
                invalid = True
            if expected is float and not math.isfinite(value):
                invalid = True
            if isinstance(value, str) and len(value) > 500:
                invalid = True
            if invalid:
                audit_failed("invalid_arguments")
                raise ValueError("invalid tool argument")
        try:
            result = spec.handler(arguments, context) if context is not None and spec.name == "research.search" else spec.handler(arguments)
        except Exception as exc:
            audit_failed(type(exc).__name__)
            raise
        self._audit(owner_id, "tool.completed", name, {
            **audit_context, "duration_ms": elapsed_ms(),
        })
        return result

    def _audit(self, owner_id, event, name, extra=None):
        # Persist only bounded metadata. Arguments and results are intentionally
        # excluded even if a future caller accidentally adds them to the payload.
        string_limits = {
            "permission": 32, "risk": 32, "decision": 32,
            "reason_code": 48, "error_type": 64,
        }
        safe_extra = {}
        for key, limit in string_limits.items():
            value = (extra or {}).get(key)
            if isinstance(value, str):
                safe_extra[key] = value[:limit]
        duration = (extra or {}).get("duration_ms")
        if isinstance(duration, int) and not isinstance(duration, bool) and 0 <= duration <= 1_000_000_000:
            safe_extra["duration_ms"] = duration
        safe_name = name[:80] if isinstance(name, str) else "unknown"
        details = {"tool": safe_name, **safe_extra}
        with self.engine.db() as c:
            c.execute("INSERT INTO api_activity VALUES(?,?,?,?,?)",
                      (uid("act"), owner_id, event, json.dumps(details, sort_keys=True), now()))

    def _memory_search(self, args):
        return self.engine.search_memories(args["query"], limit=20)

    def _claims(self, args):
        return self.engine.list_claims(args["state"], limit=100)
