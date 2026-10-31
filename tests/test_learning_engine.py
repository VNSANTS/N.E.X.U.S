import tempfile
import unittest
from pathlib import Path

from nexus_learning import LearningEngine


class LearningEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = LearningEngine(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_separate_memory_types(self):
        mid = self.engine.add_memory("episodic", "Test event", "A test happened")
        with self.engine.db() as db:
            row = db.execute("SELECT kind FROM memories WHERE id=?", (mid,)).fetchone()
        self.assertEqual(row["kind"], "episodic")

    def test_claim_requires_source_and_explicit_review(self):
        source = self.engine.add_source("https://example.org", "Example")
        claim = self.engine.propose_claim("Example claim", [source])
        with self.engine.db() as db:
            row = db.execute("SELECT state FROM claims WHERE id=?", (claim,)).fetchone()
        self.assertEqual(row["state"], "proposed")
        with self.assertRaises(ValueError):
            self.engine.review_claim(claim, "validated", "Looks good")
        self.engine.review_claim(claim, "validated", "Checked against source", .8)

    def test_task_priority_is_transparent_and_bounded(self):
        high = self.engine.add_task("High", .9, .9, .9, .8, .1, .0)
        low = self.engine.add_task("Low", .1, .1, .1, .1, .8, .2)
        ordered = self.engine.prioritized_tasks()
        self.assertEqual(ordered[0]["id"], high)
        self.assertEqual(ordered[-1]["id"], low)

    def test_invalid_memory_type_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.add_memory("random", "Title", "Body")


if __name__ == "__main__":
    unittest.main()
