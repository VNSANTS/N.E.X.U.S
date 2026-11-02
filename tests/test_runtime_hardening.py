import json
import tempfile
import unittest
from pathlib import Path

from nexus_learning import LearningEngine
from nexus_learning.providers.base import ModelResponse
from nexus_learning.providers.errors import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
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

    def test_provider_errors_have_stable_safe_codes(self):
        cases = (
            (ProviderConfigurationError(), "provider_configuration_invalid", False),
            (ProviderAuthenticationError(), "provider_authentication_failed", False),
            (ProviderRateLimitError(retry_after=2.5), "provider_rate_limited", True),
            (ProviderTimeoutError(), "provider_timeout", True),
            (ProviderUnavailableError(), "provider_unavailable", True),
            (ProviderResponseError(), "provider_response_invalid", False),
        )
        for error, code, retryable in cases:
            with self.subTest(code=code):
                self.assertEqual(error.code, code)
                self.assertEqual(error.retryable, retryable)
                self.assertNotIn("sk-", error.safe_summary)

    def test_typed_provider_failure_persists_only_safe_diagnostics(self):
        class RateLimitedProvider:
            def generate(self, messages, *, max_tokens=800, timeout=30):
                raise ProviderRateLimitError(retry_after=2.5)

        runtime = TaskRuntime(self.engine, RateLimitedProvider())
        task = runtime.run(runtime.submit("Test rate limit"))
        self.assertEqual(task["state"], "failed")
        self.assertEqual(
            task["error"],
            "provider_rate_limited: Provider rate limit exceeded.",
        )
        details = json.loads(task["events"][-1]["details"])
        self.assertEqual(details["error_code"], "provider_rate_limited")
        self.assertTrue(details["retryable"])
        self.assertEqual(details["retry_after"], 2.5)

    def test_rate_limit_retry_after_must_be_finite_and_non_negative(self):
        for value in (-1, float("inf"), float("nan"), True, 10 ** 10000):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ProviderRateLimitError(retry_after=value)


if __name__ == "__main__":
    unittest.main()
