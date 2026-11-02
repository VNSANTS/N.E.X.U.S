import unittest

from nexus_learning.context import ContextRetriever
from nexus_learning.engine import LearningEngine


class BrokenSemanticIndex:
    def search(self, query, *, limit=5):
        raise RuntimeError("embedding provider unavailable")


class ContextRetrieverTests(unittest.TestCase):
    def setUp(self):
        self.engine = LearningEngine(":memory:")

    def tearDown(self):
        self.engine.close()

    def test_lexical_retrieval_ranks_title_matches_and_explains_match(self):
        self.engine.add_memory("episodic", "Projeto ponte", "Registro de construção")
        newest_but_weak = self.engine.add_memory("semantic", "Anotações", "A ponte aparece em uma frase")
        retriever = ContextRetriever(self.engine, max_items=5)
        result = retriever.retrieve_detailed("ponte")
        self.assertEqual(result["query_terms"], ["ponte"])
        self.assertEqual(result["items"][0]["kind"], "memory")
        self.assertGreater(result["items"][0]["score"], 0)
        self.assertIn("ponte", result["items"][0]["matched_terms"])
        self.assertEqual(result["lexical_candidates"], 2)
        self.assertIn(newest_but_weak, [item["id"] for item in result["items"]])

    def test_validated_claim_is_grouped_once_with_all_source_excerpts(self):
        source_a = self.engine.add_source("https://a.example.org/page", "Source A")
        source_b = self.engine.add_source("https://b.example.net/page", "Source B")
        claim = self.engine.propose_claim(
            "Alpha technology improves evidence quality",
            [source_a, source_b],
            {source_a: "Excerpt from source A", source_b: "Excerpt from source B"})
        self.engine.review_claim(claim, "validated", "Reviewed both sources", .9)
        result = ContextRetriever(self.engine).retrieve_detailed("alpha technology")
        claims = [item for item in result["items"] if item["kind"] == "validated_claim"]
        self.assertEqual(len(claims), 1)
        self.assertIn("a.example.org", claims[0]["text"])
        self.assertIn("b.example.net", claims[0]["text"])
        self.assertEqual(claims[0]["id"], claim)

    def test_archived_memories_and_unvalidated_claims_are_not_retrieved(self):
        memory = self.engine.add_memory("episodic", "Hidden topic", "Secret context")
        self.engine.archive_memory(memory)
        source = self.engine.add_source("https://example.org", "Example")
        self.engine.propose_claim("Hidden topic claim", [source], {source: "Excerpt"})
        items = ContextRetriever(self.engine).retrieve("hidden topic")
        self.assertEqual(items, [])

    def test_lexical_preview_does_not_call_semantic_provider(self):
        self.engine.add_memory("semantic", "Local preview", "A safe local context")
        class MustNotRun:
            def search(self, *args, **kwargs):
                raise AssertionError("lexical preview must not call semantic provider")
        result = ContextRetriever(self.engine, semantic_index=MustNotRun()).retrieve_detailed(
            "local preview", include_semantic=False)
        self.assertFalse(result["used_semantic"])
        self.assertEqual(result["semantic_candidates"], 0)
        self.assertTrue(result["items"])

    def test_semantic_failure_does_not_block_lexical_fallback(self):
        self.engine.add_memory("semantic", "Database indexing", "SQLite query planning")
        result = ContextRetriever(self.engine, semantic_index=BrokenSemanticIndex()).retrieve_detailed("database")
        self.assertTrue(any(item["kind"] == "memory" for item in result["items"]))
        self.assertFalse(result["used_semantic"])

    def test_retrieval_limits_and_query_types_are_validated(self):
        with self.assertRaises(ValueError):
            ContextRetriever(self.engine, max_items=0)
        with self.assertRaises(ValueError):
            ContextRetriever(self.engine, max_chars=10)
        retriever = ContextRetriever(self.engine)
        with self.assertRaises(TypeError):
            retriever.retrieve(123)
        self.assertEqual(retriever.retrieve("a e"), [])


if __name__ == "__main__":
    unittest.main()
