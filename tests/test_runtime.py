import tempfile
import unittest
from pathlib import Path

from nexus_learning import LearningEngine
from nexus_learning.policy import PolicyEngine, READ, WRITE_REVERSIBLE, SENSITIVE
from nexus_learning.providers.mock import MockProvider
from nexus_learning.runtime import TaskRuntime


class PolicyTests(unittest.TestCase):
    def test_unknown_tool_is_denied(self):
        decision = PolicyEngine().evaluate("browser", READ)
        self.assertFalse(decision.allowed)

    def test_read_requires_allowlist(self):
        policy = PolicyEngine(allowed_tools={"search"})
        self.assertTrue(policy.evaluate("search", READ).allowed)

    def test_writes_and_sensitive_actions_require_approval(self):
        policy = PolicyEngine(allowed_tools={"save", "send"})
        self.assertTrue(policy.evaluate("save", WRITE_REVERSIBLE).requires_approval)
        self.assertTrue(policy.evaluate("send", SENSITIVE).requires_approval)
        self.assertTrue(policy.evaluate("send", SENSITIVE, approved=True).allowed)

    def test_unknown_permission_is_denied(self):
        decision = PolicyEngine(allowed_tools={"x"}).evaluate("x", "ROOT")
        self.assertFalse(decision.allowed)

    def test_truthy_non_boolean_values_never_grant_permissions(self):
        policy = PolicyEngine(allowed_tools={"send", "save"})
        for approval in ("false", "true", 1):
            with self.subTest(approval=approval):
                decision = policy.evaluate("send", SENSITIVE, approved=approval)
                self.assertFalse(decision.allowed)
                self.assertTrue(decision.requires_approval)

        with self.assertRaises(ValueError):
            PolicyEngine(allowed_tools={"save"}, allow_reversible="false")


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = LearningEngine(Path(self.tmp.name) / "runtime.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_mock_runtime_completes_and_audits(self):
        runtime = TaskRuntime(self.engine, MockProvider("Olá do N.E.X.U.S."))
        task_id = runtime.submit("Oi")
        task = runtime.run(task_id)
        self.assertEqual(task["state"], "completed")
        self.assertEqual(task["result"], "Olá do N.E.X.U.S.")
        self.assertEqual(task["provider"], "mock")
        self.assertEqual([e["event"] for e in task["events"]],
                         ["task.received", "task.started", "task.completed"])

    def test_empty_and_oversized_input_rejected(self):
        runtime = TaskRuntime(self.engine, MockProvider(), max_input_chars=4)
        with self.assertRaises(ValueError):
            runtime.submit(" ")
        with self.assertRaises(ValueError):
            runtime.submit("mensagem")

    def test_provider_failure_is_recorded(self):
        class BrokenProvider:
            def generate(self, messages, **kwargs):
                raise TimeoutError("provider timeout")
        runtime = TaskRuntime(self.engine, BrokenProvider())
        task_id = runtime.submit("Teste")
        task = runtime.run(task_id)
        self.assertEqual(task["state"], "failed")
        self.assertEqual(task["error"], "TimeoutError: provider execution failed")

    def test_task_cannot_be_run_twice(self):
        runtime = TaskRuntime(self.engine, MockProvider())
        task_id = runtime.submit("Teste")
        runtime.run(task_id)
        with self.assertRaises(ValueError):
            runtime.run(task_id)

    def test_pre_generation_pipeline_failure_closes_received_task_safely(self):
        runtime = TaskRuntime(self.engine, MockProvider())
        task_id = runtime.submit("Teste")
        self.assertTrue(runtime.fail_unstarted(task_id, "agent_pipeline_failed"))
        task = runtime.get(task_id)
        self.assertEqual(task["state"], "failed")
        self.assertEqual(task["error"], "agent_pipeline_failed: task preparation failed")
        self.assertFalse(runtime.fail_unstarted(task_id, "agent_pipeline_failed"))

    def test_stream_disconnect_cancels_task_and_preserves_partial_result_out_of_history(self):
        class StreamingProvider:
            provider_name = "ollama"
            model = "qwen-test"
            def stream_generate(self, messages, *, max_tokens, timeout, cancel_event):
                yield "partial"
                while not cancel_event.is_set():
                    yield "more"
        runtime = TaskRuntime(self.engine, StreamingProvider())
        task_id = runtime.submit("Stream test")
        stream = runtime.run_stream(task_id)
        self.assertEqual(next(stream), "partial")
        stream.close()
        task = runtime.get(task_id)
        self.assertEqual(task["state"], "cancelled")
        self.assertIsNone(task["result"])


if __name__ == "__main__":
    unittest.main()
