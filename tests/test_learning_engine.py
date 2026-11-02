import tempfile
import unittest
from pathlib import Path

from nexus_learning import LearningEngine
from nexus_learning.ingestion import DocumentIngestor


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

    def test_memory_metadata_must_be_bounded_finite_json_object(self):
        with self.assertRaises(ValueError):
            self.engine.add_memory("semantic", "Title", "Body", ["not", "an", "object"])
        with self.assertRaises(ValueError):
            self.engine.add_memory("semantic", "Title", "Body", {"score": float("nan")})
        with self.assertRaises(ValueError):
            self.engine.add_memory("semantic", "Title", "Body", {"large": "x" * 9000})
        memory_id = self.engine.add_memory("semantic", "Title", "Body", {"origin": "user"})
        self.assertEqual(self.engine.search_memories()[0]["id"], memory_id)

    def test_memory_text_and_search_parameters_are_validated(self):
        for title, body in ((None, "Body"), ("Title", None), ("x" * 501, "Body"), ("Title", "x" * 12001)):
            with self.assertRaises(ValueError):
                self.engine.add_memory("episodic", title, body)
        with self.assertRaises(ValueError):
            self.engine.search_memories(query=123)
        with self.assertRaises(ValueError):
            self.engine.search_memories(limit=True)

    def test_claim_requires_source_and_explicit_review(self):
        unsourced = self.engine.propose_claim("Unsourced claim")
        with self.assertRaises(ValueError):
            self.engine.review_claim(unsourced, "validated", "No supporting source", .8)
        source = self.engine.add_source("https://example.org", "Example")
        claim = self.engine.propose_claim("Example claim", [source], {source: "Evidence excerpt"})
        self.assertEqual(self.engine.get_claim(claim)["sources"][0]["excerpt"], "Evidence excerpt")
        self.assertEqual(self.engine.get_claim(claim)["state"], "proposed")
        with self.assertRaises(ValueError):
            self.engine.review_claim(claim, "validated", "Looks good")
        self.engine.review_claim(claim, "validated", "Checked against source", .8)
        self.assertEqual(self.engine.get_claim(claim)["state"], "validated")

    def test_claim_validation_requires_http_source_and_nonempty_excerpt(self):
        local_source = self.engine.add_source("local://notes", "Local notes")
        claim = self.engine.propose_claim("A sourced claim", [local_source], {local_source: "Evidence"})
        quality = self.engine.assess_claim_evidence(claim)
        self.assertFalse(quality["complete"])
        self.assertIn("source_url_not_http", quality["issues"])
        with self.assertRaises(ValueError):
            self.engine.review_claim(claim, "validated", "Reviewed", .8)
        web_source = self.engine.add_source("https://example.org/page", "Web source")
        claim2 = self.engine.propose_claim("Another claim", [web_source])
        with self.assertRaises(ValueError):
            self.engine.review_claim(claim2, "validated", "No excerpt", .8)

    def test_claim_confidence_rejects_boolean_and_nonfinite_values(self):
        source = self.engine.add_source("https://example.org", "Example")
        claim = self.engine.propose_claim("Example claim", [source], {source: "Evidence excerpt"})
        for confidence in (True, float("nan"), float("inf"), -0.1, 1.1):
            with self.assertRaises(ValueError):
                self.engine.review_claim(claim, "validated", "Reviewed", confidence)

    def test_claim_evidence_report_exposes_semantic_verification_limit(self):
        source = self.engine.add_source("https://example.org", "Example")
        claim = self.engine.propose_claim("Example claim", [source], {source: "Evidence excerpt"})
        report = self.engine.get_claim(claim)["evidence_quality"]
        self.assertTrue(report["complete"])
        self.assertIn("do not establish", report["limitation"])
        self.assertEqual(self.engine.list_claims()[0]["evidence_quality"]["claim_id"], claim)

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


    def test_text_ingestion_preserves_source_and_chunks(self):
        ingestor = DocumentIngestor(self.engine)
        text = ("Primeiro parágrafo sobre memória.\\n" * 30) + ("Segundo parágrafo sobre aprendizado.\\n" * 30)
        result = ingestor.ingest_text(text, "local://sample.txt", "Sample")
        self.assertFalse(result["duplicate"])
        self.assertGreater(result["chunks"], 1)
        hits = ingestor.search("aprendizado")
        self.assertTrue(hits)
        self.assertEqual(hits[0]["uri"], "local://sample.txt")

    def test_duplicate_document_is_not_stored_twice(self):
        ingestor = DocumentIngestor(self.engine)
        first = ingestor.ingest_text("Conteúdo idêntico", "local://one.txt")
        second = ingestor.ingest_text("Conteúdo idêntico", "local://two.txt")
        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(first["document_id"], second["document_id"])
        self.assertEqual(self.engine.stats()["sources"], 1)

    def test_ingestion_rejects_empty_and_oversized_text(self):
        ingestor = DocumentIngestor(self.engine, max_bytes=20)
        with self.assertRaises(ValueError):
            ingestor.ingest_text("   ", "local://empty.txt")
        with self.assertRaises(ValueError):
            ingestor.ingest_text("x" * 30, "local://large.txt")

    def test_ingestion_rejects_invalid_chunk_settings(self):
        ingestor = DocumentIngestor(self.engine)
        with self.assertRaises(ValueError):
            ingestor.ingest_text("Texto válido", "local://x.txt", chunk_size=50)

    def test_invalid_memory_type_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.add_memory("random", "Title", "Body")


if __name__ == "__main__":
    unittest.main()
