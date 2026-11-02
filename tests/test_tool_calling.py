import json
import tempfile
import unittest
from pathlib import Path

from nexus_learning import LearningEngine
from nexus_learning.policy import READ
from nexus_learning.providers.base import ModelResponse, ToolCall
from nexus_learning.runtime import TaskRuntime
from nexus_learning.tools import ToolRegistry, ToolSpec


class ToolCallingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = LearningEngine(Path(self.tmp.name) / "tools.db")
        self.registry = ToolRegistry(self.engine)

    def tearDown(self):
        self.engine.close()
        self.tmp.cleanup()

    def test_registry_exports_only_read_tools_as_json_schema(self):
        self.registry.register(ToolSpec("safe.lookup", "Look up a value", READ,
                                        {"query": str, "limit": int}, lambda args: args))
        self.registry.register(ToolSpec("sensitive.send", "Send a message", "SENSITIVE",
                                        {"body": str}, lambda args: args))
        tools = self.registry.model_tools()
        self.assertEqual([tool["function"]["name"] for tool in tools],
                         ["memory.search", "knowledge.claims", "safe.lookup"])
        schema = next(t["function"]["parameters"] for t in tools
                      if t["function"]["name"] == "safe.lookup")
        self.assertEqual(schema["required"], ["query", "limit"])
        self.assertEqual(schema["properties"]["limit"]["type"], "integer")

    def test_runtime_executes_bounded_read_tool_then_returns_model_answer(self):
        class ToolProvider:
            provider_name = "test"
            model = "tool-model"
            supports_tools = True
            def __init__(self):
                self.calls = []
            def generate(self, messages, *, tools=None, **kwargs):
                self.calls.append((messages, tools))
                if len(self.calls) == 1:
                    return ModelResponse("", "test", "tool-model", tool_calls=(
                        ToolCall("call-1", "safe.lookup", {"query": "NEXUS"}),))
                self.assert_untrusted = messages[-1]["content"]
                return ModelResponse("Found it.", "test", "tool-model")

        observed = []
        self.registry.register(ToolSpec("safe.lookup", "Look up a value", READ,
                                        {"query": str}, lambda args: observed.append(args) or {"value": "result"}))
        provider = ToolProvider()
        runtime = TaskRuntime(self.engine, provider, tool_registry=self.registry)
        task_id = runtime.submit("Find NEXUS")
        task = runtime.run(task_id, owner_id="user-1")
        self.assertEqual(task["state"], "completed")
        self.assertEqual(task["result"], "Found it.")
        self.assertEqual(observed, [{"query": "NEXUS"}])
        self.assertIn("untrusted", provider.assert_untrusted.lower())
        self.assertEqual(len(provider.calls), 2)
        self.assertTrue(provider.calls[0][1])
        with self.engine.db() as c:
            names = [json.loads(r[0])["tool"] for r in c.execute(
                "SELECT details FROM api_activity WHERE event='tool.completed'")]
        self.assertEqual(names, ["safe.lookup"])

    def test_sensitive_tool_is_not_exposed_or_run_from_model_call(self):
        class SensitiveProvider:
            provider_name = "test"
            model = "test"
            supports_tools = True
            def generate(self, messages, **kwargs):
                return ModelResponse("", "test", "test", tool_calls=(
                    ToolCall("sensitive-1", "research.search", {"query": "secret", "depth": "quick"}),))
        self.registry.register(ToolSpec("research.search", "Search", "SENSITIVE",
                                        {"query": str, "depth": str}, lambda args: args))
        runtime = TaskRuntime(self.engine, SensitiveProvider(), tool_registry=self.registry)
        task = runtime.run(runtime.submit("Search the web"), owner_id="user-1")
        self.assertEqual(task["state"], "failed")
        self.assertNotIn("secret", json.dumps(task["events"]))

    def test_tool_result_is_bounded_and_explicitly_untrusted(self):
        class LargeResultProvider:
            provider_name = "test"
            model = "test"
            supports_tools = True
            def __init__(self): self.last_tool_result = ""; self.calls = 0
            def generate(self, messages, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    return ModelResponse("", "test", "test", tool_calls=(
                        ToolCall("large", "safe.lookup", {"query": "x"}),))
                self.last_tool_result = messages[-1]["content"]
                return ModelResponse("done", "test", "test")
        self.registry.register(ToolSpec("safe.lookup", "Look up", READ,
                                        {"query": str}, lambda args: {"text": "á" * 12000}))
        provider = LargeResultProvider()
        runtime = TaskRuntime(self.engine, provider, tool_registry=self.registry)
        task = runtime.run(runtime.submit("bounded"), owner_id="user-1")
        self.assertEqual(task["state"], "completed")
        # The fake stores the user data only after it receives it on the next round.
        result_message = provider.last_tool_result
        self.assertLess(len(result_message.encode("utf-8")), 9000)
        self.assertIn("UNTRUSTED TOOL RESULT", result_message)

    def test_repeated_call_and_round_limit_fail_closed(self):
        class RepeatingProvider:
            provider_name = "test"
            model = "test"
            supports_tools = True
            calls = 0
            def generate(self, messages, **kwargs):
                self.calls += 1
                return ModelResponse("", "test", "test", tool_calls=(
                    ToolCall("call-" + str(self.calls), "safe.lookup", {"query": "x"}),))
        runs = []
        self.registry.register(ToolSpec("safe.lookup", "Look up", READ,
                                        {"query": str}, lambda args: runs.append(args) or {"ok": True}))
        provider = RepeatingProvider()
        runtime = TaskRuntime(self.engine, provider, tool_registry=self.registry,
                              max_tool_rounds=2)
        task = runtime.run(runtime.submit("repeat"), owner_id="user-1")
        self.assertEqual(task["state"], "failed")
        self.assertEqual(len(runs), 2)
        self.assertEqual(provider.calls, 3)

    def test_duplicate_provider_call_id_is_rejected_before_second_execution(self):
        class DuplicateProvider:
            provider_name = "test"
            model = "test"
            supports_tools = True
            calls = 0
            def generate(self, messages, **kwargs):
                self.calls += 1
                return ModelResponse("", "test", "test", tool_calls=(
                    ToolCall("duplicate", "safe.lookup", {"query": "x"}),))
        runs = []
        self.registry.register(ToolSpec("safe.lookup", "Look up", READ,
                                        {"query": str}, lambda args: runs.append(args) or {"ok": True}))
        provider = DuplicateProvider()
        runtime = TaskRuntime(self.engine, provider, tool_registry=self.registry)
        task = runtime.run(runtime.submit("duplicate"), owner_id="user-1")
        self.assertEqual(task["state"], "failed")
        self.assertEqual(provider.calls, 2)
        self.assertEqual(len(runs), 1)

    def test_streaming_path_remains_cancellable_and_withholds_tool_schemas(self):
        class StreamingToolProvider:
            provider_name = "test"
            model = "stream-test"
            supports_tools = True
            def generate(self, messages, **kwargs):
                raise AssertionError("non-streaming generation must not run on SSE")
            def stream_generate(self, messages, *, max_tokens, timeout, cancel_event):
                yield "streamed answer"
        provider = StreamingToolProvider()
        runtime = TaskRuntime(self.engine, provider, tool_registry=self.registry,
                              tool_calling_enabled=True)
        task_id = runtime.submit("answer")
        self.assertEqual("".join(runtime.run_stream(task_id)), "streamed answer")
        self.assertEqual(runtime.get(task_id)["state"], "completed")


if __name__ == "__main__":
    unittest.main()
