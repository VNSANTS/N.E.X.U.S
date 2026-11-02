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
