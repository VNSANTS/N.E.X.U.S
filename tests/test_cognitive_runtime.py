import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from nexus_learning import LearningEngine, CognitiveAdaptation
from nexus_learning.runtime import TaskRuntime


class CapturingProvider:
    def __init__(self):
        self.messages = None

    def generate(self, messages, **kwargs):
        self.messages = messages
        return SimpleNamespace(text="ok", provider="test", model="capture")


class CognitiveRuntimeIntegrationTests(unittest.TestCase):
    def test_runtime_injects_only_enabled_and_reviewed_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = LearningEngine(Path(tmp) / "runtime.db")
            profile = CognitiveAdaptation(engine)
            profile.set_preference("response_length", "short")
            pattern_id = profile.propose_pattern(
                "Checks assumptions before solving",
                "A repeated problem-solving behavior.",
            )
            provider = CapturingProvider()
            runtime = TaskRuntime(engine, provider, cognitive_engine=profile)

            task_id = runtime.submit("Test")
            runtime.run(task_id)
            self.assertNotIn("response_length", provider.messages[0]["content"])

            profile.review_pattern(pattern_id, "confirmed", "Confirmed by user.")
            profile.set_enabled(True)
            task_id = runtime.submit("Test again")
            runtime.run(task_id)
            system_message = provider.messages[0]["content"]
            self.assertIn("response_length: short", system_message)
            self.assertIn("Checks assumptions before solving", system_message)
            engine.close()


if __name__ == "__main__":
    unittest.main()
