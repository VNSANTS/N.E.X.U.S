"""Deterministic authorization policy for N.E.X.U.S. runtime actions."""
from dataclasses import dataclass

READ = "READ"
WRITE_REVERSIBLE = "WRITE_REVERSIBLE"
SENSITIVE = "SENSITIVE"
ALLOWED_CLASSES = {READ, WRITE_REVERSIBLE, SENSITIVE}


@dataclass(frozen=True)
class Decision:
    allowed: bool
    requires_approval: bool
    reason: str


class PolicyEngine:
    """Fail-closed policy. Model output never grants its own permissions."""

    def __init__(self, allowed_tools=(), allow_reversible=False):
        if not isinstance(allow_reversible, bool):
            raise ValueError("allow_reversible must be a boolean")
        self.allowed_tools = frozenset(allowed_tools)
        self.allow_reversible = allow_reversible

    def evaluate(self, tool_name, permission, approved=False):
        if not tool_name or tool_name not in self.allowed_tools:
            return Decision(False, False, "Tool is not allowlisted")
        if permission not in ALLOWED_CLASSES:
            return Decision(False, False, "Unknown permission class")
        if permission == READ:
            return Decision(True, False, "Allowlisted read action")
        if permission == WRITE_REVERSIBLE:
            if approved is True:
                return Decision(True, False, "Explicit approval received")
            if self.allow_reversible:
                return Decision(True, False, "Reversible writes enabled by configuration")
            return Decision(False, True, "Approval required for reversible write")
        if permission == SENSITIVE:
            if approved is True:
                return Decision(True, False, "Explicit action-specific approval received")
            return Decision(False, True, "Specific approval required for sensitive action")
        return Decision(False, False, "Denied")
