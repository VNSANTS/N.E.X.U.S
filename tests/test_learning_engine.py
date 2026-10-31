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

    def test_separate_memory_types_and_search(self):
        mid = self.engine.add_memory("episodic", "Test event", "A test happened")
        self.engine.add_memory("semantic", "Python", "A programming language")
        self.assertEqual(len(self.engine.search_memories(memory_type="episodic")), 1)
        self.assertEqual(self.engine.search_memories("programming")[0]["kind"], "semantic")
        self.assertTrue(self.engine.archive_memory(mid))
        self.assertFalse(self.engine.archive_memory(mid))

    def test_claim_requires_source_and_explicit_review(self):
        source = self.engine.add_source("https://example.org", "Example")
        claim = self.engine.propose_claim("Example claim", [source], {source: "Evidence excerpt"})
        self.assertEqual(self.engine.get_claim(claim)["sources"][0]["excerpt"], "Evidence excerpt")
        self.assertEqual(self.engine.get_claim(claim)["state"], "proposed")
        with self.assertRaises(ValueError):
            self.engine.review_claim(claim, "validated", "Looks good")
        self.engine.review_claim(claim, "validated", "Checked against source", .8)
        self.assertEqual(self.engine.get_claim(claim)["state"], "validated")

    def test_claim_rejects_unknown_source(self):
        with self.assertRaises(ValueError):
            self.engine.propose_claim("Unsupported claim", ["missing-source"])

    def test_consolidation_only_reports_candidates(self):
        a = self.engine.propose_claim("Same claim")
        b = self.engine.propose_claim("  SAME CLAIM. ")
        report = self.engine.consolidation_report()
        self.assertEqual(len(report["possible_duplicate_claim_groups"]), 1)
        self.assertEqual(set(report["possible_duplicate_claim_groups"][0]), {a, b})
        self.assertEqual(len(report["claims_without_sources"]), 2)
        self.assertIn("No automatic", report["note"])

    def test_task_priority_and_status(self):
        high = self.engine.add_task("High", .9, .9, .9, .8, .1, .0)
        low = self.engine.add_task("Low", .1, .1, .1, .1, .8, .2)
        ordered = self.engine.prioritized_tasks()
        self.assertEqual(ordered[0]["id"], high)
        self.assertEqual(ordered[-1]["id"], low)
        self.engine.set_task_status(high, "done")
        self.assertEqual(len(self.engine.prioritized_tasks()), 1)

    def test_stats(self):
        self.engine.add_memory("procedural", "Test", "Procedure")
        self.assertEqual(self.engine.stats()["memories"], 1)

    def test_invalid_memory_type_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.add_memory("random", "Title", "Body")


if __name__ == "__main__":
    unittest.main()
