import json
import unittest

from nexus_learning.engine import LearningEngine
from nexus_learning.policy import READ, SENSITIVE
from nexus_learning.tools import ToolRegistry, ToolSpec


class ToolRegistryTests(unittest.TestCase):
    def setUp(self):
        self.engine = LearningEngine(":memory:")
        self.registry = ToolRegistry(self.engine)

    def tearDown(self):
        self.engine.close()

    def test_sensitive_registered_tool_requires_explicit_action_approval(self):
        self.registry.register(ToolSpec("research.search", "Search web", SENSITIVE,
                                        {"query": str}, lambda args: {"query": args["query"]}))
        with self.assertRaises(PermissionError):
            self.registry.execute("research.search", {"query": "weather"}, owner_id="owner")
        result = self.registry.execute("research.search", {"query": "weather"},
                                       owner_id="owner", approved=True)
        self.assertEqual(result, {"query": "weather"})
        with self.engine.db() as c:
            events={row["event"] for row in c.execute("SELECT event FROM api_activity").fetchall()}
        self.assertIn("tool.completed",events)
        self.assertIn("tool.denied",events)
        with self.engine.db() as c:
            denied = c.execute(
                "SELECT details FROM api_activity WHERE event='tool.denied'"
            ).fetchone()
        details=json.loads(denied["details"])
        self.assertEqual(details["reason_code"],"approval_required")
        self.assertEqual(details["decision"],"denied")

    def test_tool_audit_records_metadata_only_and_elapsed_time(self):
        private_query = "PRIVATE TOOL ARGUMENT MUST NOT BE STORED"
        self.registry.execute("memory.search", {"query": private_query}, owner_id="owner")
        with self.engine.db() as c:
            rows = c.execute(
                "SELECT event,details FROM api_activity ORDER BY rowid ASC"
            ).fetchall()
        self.assertEqual([row["event"] for row in rows], ["tool.started", "tool.completed"])
        for row in rows:
            details = json.loads(row["details"])
            self.assertEqual(details["tool"], "memory.search")
            self.assertEqual(details["risk"], READ)
            self.assertEqual(details["permission"], READ)
            self.assertEqual(details["decision"], "allowed")
            self.assertNotIn("arguments", details)
            self.assertNotIn("result", details)
            self.assertNotIn(private_query, json.dumps(details))
        self.assertGreaterEqual(json.loads(rows[-1]["details"])["duration_ms"], 0)

    def test_audit_allowlist_discards_future_untrusted_payload_fields(self):
        self.registry._audit("owner", "tool.completed", "memory.search", {
            "permission": READ, "risk": READ, "decision": "allowed",
            "duration_ms": 12, "arguments": "PRIVATE ARGUMENT",
            "result": "PRIVATE RESULT", "prompt": "PRIVATE PROMPT",
        })
        with self.engine.db() as c:
            details = json.loads(c.execute(
                "SELECT details FROM api_activity"
            ).fetchone()["details"])
        self.assertEqual(set(details), {"tool", "permission", "risk", "decision", "duration_ms"})
        self.assertNotIn("PRIVATE", json.dumps(details))

    def test_dynamic_registration_rejects_unknown_risk_and_invalid_names(self):
        with self.assertRaises(ValueError):
            self.registry.register(ToolSpec("bad name", "x", READ, {}, lambda args: None))
        with self.assertRaises(ValueError):
            self.registry.register(ToolSpec("bad.permission", "x", "ADMIN", {}, lambda args: None))

    def test_sensitive_tool_cannot_be_downgraded_by_permission_override(self):
        with self.assertRaises(ValueError):
            self.registry.register(ToolSpec("bad.downgrade", "x", SENSITIVE, {},
                                            lambda args: None, permission=READ))

    def test_argument_schema_does_not_crash_on_non_string_values(self):
        self.registry.register(ToolSpec("read.example", "Example", READ,
                                        {"query": str}, lambda args: args))
        with self.assertRaises(ValueError):
            self.registry.execute("read.example", {"query": 9}, owner_id="owner")

    def test_non_finite_float_arguments_are_rejected_as_invalid_json(self):
        self.registry.register(ToolSpec("read.score", "Read score", READ,
                                        {"score": float}, lambda args: args))
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.registry.execute("read.score", {"score": value}, owner_id="owner")


if __name__ == "__main__":
    unittest.main()
