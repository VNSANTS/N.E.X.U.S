import unittest

from nexus_learning.model_router import ModelRouter, NoRouteAvailable


class ModelRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = ModelRouter()
        self.models = [
            {"provider": "ollama", "model": "qwen-small", "available": True,
             "allowed": True, "remote": False, "context_window": 4096,
             "latency_ms": 900, "cost_per_1k": 0, "reasoning_score": 1},
            {"provider": "gemini", "model": "flash", "available": True,
             "allowed": True, "remote": True, "budget_available": True,
             "context_window": 32768, "latency_ms": 300, "cost_per_1k": .01,
             "reasoning_score": 3},
            {"provider": "openai", "model": "unavailable", "available": False,
             "allowed": True, "remote": True, "budget_available": True,
             "context_window": 128000, "latency_ms": 100, "cost_per_1k": .001,
             "reasoning_score": 5},
        ]

    def test_classifies_simple_standard_advanced_and_research(self):
        self.assertEqual(self.router.classify("Oi"), "SIMPLE")
        self.assertEqual(self.router.classify("Como está o tempo hoje na minha região?"), "RESEARCH")
        self.assertEqual(self.router.classify("Quais as notícias atuais sobre clima?"), "RESEARCH")
        self.assertEqual(self.router.classify("Explique como funciona uma bateria"), "STANDARD")
        self.assertEqual(self.router.classify("Compare e avalie as alternativas com riscos e plano"), "ADVANCED")
        self.assertEqual(self.router.classify("Pesquise fontes oficiais sobre o assunto"), "RESEARCH")
        self.assertEqual(self.router.classify("Pesquise referências científicas atuais"), "RESEARCH")

    def test_simple_prefers_low_cost_local_candidate(self):
        route = self.router.choose("Oi", self.models)
        self.assertEqual((route.provider, route.model), ("ollama", "qwen-small"))

    def test_advanced_prefers_reasoning_capability_and_skips_unavailable(self):
        route = self.router.choose("Compare e avalie as alternativas", self.models,
                                   remote_allowed=True)
        self.assertEqual((route.provider, route.model), ("gemini", "flash"))

    def test_research_requires_explicit_search_capability(self):
        models = [dict(self.models[1], capabilities={"chat": True, "research": False})]
        with self.assertRaises(NoRouteAvailable):
            self.router.choose("Pesquise fontes oficiais", models)

    def test_remote_candidate_fails_closed_without_budget_authorization(self):
        models = [dict(self.models[1], budget_available=False)]
        with self.assertRaises(NoRouteAvailable):
            self.router.choose("Explique isso", models)

    def test_fallback_cannot_cross_local_remote_privacy_boundary(self):
        fallback = self.router.fallback(self.models, failed={"gemini/flash"}, remote=False)
        self.assertEqual(fallback.model, "qwen-small")
        with self.assertRaises(NoRouteAvailable):
            self.router.fallback(self.models, failed={"ollama/qwen-small"}, remote=False)

    def test_context_requirement_rejects_too_small_model(self):
        with self.assertRaises(NoRouteAvailable):
            self.router.choose("Explique isso", self.models, estimated_context=5000,
                               remote_allowed=False)

    def test_malformed_candidate_metadata_is_ignored_and_bad_query_is_rejected(self):
        route = self.router.choose("Oi", [{"provider": None, "model": 4,
            "available": True, "allowed": True}, self.models[0]])
        self.assertEqual(route.provider, "ollama")
        with self.assertRaises(ValueError):
            self.router.choose(42, self.models)
        with self.assertRaises(NoRouteAvailable):
            self.router.choose("Compare alternativas", [dict(self.models[0], reasoning_score="high")])

    def test_fallback_obeys_cost_and_context_limits(self):
        with self.assertRaises(NoRouteAvailable):
            self.router.fallback(self.models, failed={"ollama/qwen-small"}, remote=False)
        with self.assertRaises(NoRouteAvailable):
            self.router.fallback([dict(self.models[1], remote=False)], failed=set(),
                                 remote=False, max_cost_per_1k=0.001)


if __name__ == "__main__":
    unittest.main()
