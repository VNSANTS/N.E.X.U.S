import json
import tempfile
import unittest
from pathlib import Path

from nexus_learning import LearningEngine
from nexus_learning.providers.base import ModelResponse
from nexus_learning.runtime import TaskRuntime


class InMemoryDatabaseTests(unittest.TestCase):
    def test_memory_database_survives_short_lived_connections(self):
        engine = LearningEngine(":memory:")
        try:
            memory_id = engine.add_memory("semantic", "N.E.X.U.S.", "SQLite memory test")
            self.assertTrue(memory_id.startswith("mem_"))
            self.assertEqual(engine.stats()["memories"], 1)
            self.assertEqual(engine.search_memories("SQLite")[0]["id"], memory_id)
        finally:
            engine.close()


class RuntimeHardeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = LearningEngine(Path(self.tmp.name) / "runtime.db")

    def tearDown(self):
        self.engine.close()
        self.tmp.cleanup()

    def test_provider_exception_message_is_not_persisted(self):
        secret_like_value = "sk-test-secret-must-not-be-stored"

        class FailingProvider:
            def generate(self, messages, *, max_tokens=800, timeout=30):
                raise RuntimeError("authorization header contained " + secret_like_value)

        runtime = TaskRuntime(self.engine, FailingProvider())
        task = runtime.run(runtime.submit("Test error handling"))

        self.assertEqual(task["state"], "failed")
        self.assertEqual(task["error"], "RuntimeError: provider execution failed")
        self.assertNotIn(secret_like_value, json.dumps(task))
        self.assertEqual(task["events"][-1]["event"], "task.failed")

    def test_running_task_cannot_be_claimed_again_reentrantly(self):
        class ReentrantProvider:
            runtime = None
            task_id = None
            reentry_rejected = False

            def generate(self, messages, *, max_tokens=800, timeout=30):
                try:
                    self.runtime.run(self.task_id)
                except ValueError as exc:
                    self.reentry_rejected = "running" in str(exc)
                if not self.reentry_rejected:
                    raise AssertionError("the running task was claimable more than once")
                return ModelResponse("completed once", "test", "reentrant-test")

        provider = ReentrantProvider()
        runtime = TaskRuntime(self.engine, provider)
        task_id = runtime.submit("Test duplicate execution")
        provider.runtime = runtime
        provider.task_id = task_id

        task = runtime.run(task_id)
        self.assertTrue(provider.reentry_rejected)
        self.assertEqual(task["state"], "completed")
        self.assertEqual(task["result"], "completed once")
        self.assertEqual(
            [event["event"] for event in task["events"]],
            ["task.received", "task.started", "task.completed"],
        )

    def test_runtime_limits_must_be_positive_integers(self):
        with self.assertRaises(ValueError):
            TaskRuntime(self.engine, object(), max_input_chars=0)
        with self.assertRaises(ValueError):
            TaskRuntime(self.engine, object(), max_output_chars=-1)


if __name__ == "__main__":
    unittest.main()
