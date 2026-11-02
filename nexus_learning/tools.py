"""Typed allowlisted read tools; no arbitrary shell or filesystem execution."""
from dataclasses import dataclass
import json
import re

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
        if permission not in {READ, WRITE_REVERSIBLE, SENSITIVE}:
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

    def execute(self, name, arguments, *, owner_id, approved=False, context=None):
        spec = self._tools.get(name)
        decision = self.policy.evaluate(name, (spec.permission or spec.risk) if spec else READ, approved)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        if spec is None:
            raise KeyError("unknown tool")
        self._audit(owner_id, "tool.started", name)
        if not isinstance(arguments, dict) or set(arguments) != set(spec.parameters):
            self._audit(owner_id, "tool.failed", name, {"error_type": "invalid_arguments"})
            raise ValueError("tool arguments do not match its schema")
        for key, expected in spec.parameters.items():
            value = arguments[key]
            invalid = not isinstance(value, expected)
            if expected is int and isinstance(value, bool):
                invalid = True
            if isinstance(value, str) and len(value) > 500:
                invalid = True
            if invalid:
                self._audit(owner_id, "tool.failed", name, {"error_type": "invalid_arguments"})
                raise ValueError("invalid tool argument")
        try:
            result = spec.handler(arguments, context) if context is not None and spec.name == "research.search" else spec.handler(arguments)
        except Exception as exc:
            self._audit(owner_id, "tool.failed", name, {"error_type": type(exc).__name__})
            raise
        self._audit(owner_id, "tool.completed", name)
        return result

    def _audit(self, owner_id, event, name, extra=None):
        details = {"tool": name, **(extra or {})}
        with self.engine.db() as c:
            c.execute("INSERT INTO api_activity VALUES(?,?,?,?,?)",
                      (uid("act"), owner_id, event, json.dumps(details, sort_keys=True), now()))

    def _memory_search(self, args):
        return self.engine.search_memories(args["query"], limit=20)

    def _claims(self, args):
        return self.engine.list_claims(args["state"], limit=100)
