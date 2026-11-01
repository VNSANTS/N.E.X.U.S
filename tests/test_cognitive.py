import tempfile
import unittest
from pathlib import Path

from nexus_learning import LearningEngine
from nexus_learning.cognitive import CognitiveAdaptation


class CognitiveAdaptationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = LearningEngine(Path(self.tmp.name) / "cognitive.db")
        self.cognitive = CognitiveAdaptation(self.engine)

    def tearDown(self):
        self.engine.close()
        self.tmp.cleanup()

    def test_disabled_by_default_and_context_is_empty(self):
        self.assertFalse(self.cognitive.enabled())
        self.assertEqual(self.cognitive.build_context(), "")

    def test_explicit_preferences_only_and_context_requires_opt_in(self):
        self.cognitive.set_preference("response_length", "short")
        self.assertEqual(self.cognitive.build_context(), "")
        self.cognitive.set_enabled(True)
        self.assertIn("response_length: short", self.cognitive.build_context())

    def test_rejects_unknown_or_inferred_preferences(self):
        with self.assertRaises(ValueError):
            self.cognitive.set_preference("personality", "analytical")
        with self.assertRaises(ValueError):
            self.cognitive.set_preference("challenge_level", "genius")
        with self.assertRaises(ValueError):
            self.cognitive.set_preference("response_length", "short", source="model")

    def test_patterns_require_review_before_context_use(self):
        pattern_id = self.cognitive.propose_pattern(
            "Questions assumptions before accepting a problem",
            "Repeatedly challenged missing constraints in problem-solving discussions.",
            confidence=0.7,
        )
        self.cognitive.set_enabled(True)
        self.assertNotIn("Questions assumptions", self.cognitive.build_context())
        self.cognitive.review_pattern(pattern_id, "confirmed", "User confirmed this is useful.")
        self.assertIn("Questions assumptions", self.cognitive.build_context())

    def test_rejected_patterns_are_not_used(self):
        pattern_id = self.cognitive.propose_pattern("Prefers examples", "Observed in several tasks.")
        self.cognitive.review_pattern(pattern_id, "rejected", "Not a stable preference.")
        self.cognitive.set_enabled(True)
        self.assertNotIn("Prefers examples", self.cognitive.build_context())

    def test_invalid_pattern_and_review_rejected(self):
        with self.assertRaises(ValueError):
            self.cognitive.propose_pattern("", "reason")
        with self.assertRaises(ValueError):
            self.cognitive.propose_pattern("pattern", "")
        with self.assertRaises(ValueError):
            self.cognitive.propose_pattern("pattern", "reason", confidence=1.1)

    def test_disabling_removes_context_without_deleting_profile(self):
        self.cognitive.set_preference("challenge_level", "demanding")
        self.cognitive.set_enabled(True)
        self.assertIn("demanding", self.cognitive.build_context())
        self.cognitive.set_enabled(False)
        self.assertEqual(self.cognitive.build_context(), "")
        self.assertEqual(self.cognitive.list_preferences()[0]["value"], "demanding")


if __name__ == "__main__":
    unittest.main()
