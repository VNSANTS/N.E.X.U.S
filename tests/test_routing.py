import json
import unittest

from nexus_learning.model_router import ModelRouter, NoRouteAvailable
from nexus_learning.routing import FallbackProvider, ModelRoutingService
from nexus_learning.providers.errors import ProviderUnavailableError
from nexus_learning.providers.base import ModelResponse


class FakeProvider:
    def __init__(self, name, model, *, fail=False, chunks=None):
        self.provider_name, self.model = name, model
        self.fail, self.chunks = fail, chunks or ["ok"]

    def generate(self, messages, **kwargs):
        if self.fail:
            raise ProviderUnavailableError()
        return ModelResponse("ok", self.provider_name, self.model)

    def stream_generate(self, messages, **kwargs):
        if self.fail:
            raise ProviderUnavailableError()
        yield from self.chunks


class FakeManager:
    def __init__(self, env, providers, models):
        self.env, self.providers, self.models = env, providers, models
        self.checked = []

    def selected(self):
        return self.providers["ollama/qwen-small"]

    def build(self, name, model):
        return self.providers[f"{name}/{model}"]

    def list_models(self, name):
        return self.models[name]

    def check(self, name):
        self.checked.append(name)
        return {"available": True}

    def _remote_enabled(self, name):
        return self.env.get("NEXUS_ENABLE_REMOTE_PROVIDER") == "true" and name in {
            item.strip() for item in self.env.get("NEXUS_REMOTE_PROVIDERS", "").split(",")}


class FakeBudget:
    def __init__(self, enabled=False):
        self.enabled = enabled

    def settings(self):
        return {"enabled": self.enabled, "input_usd_per_million": 1 if self.enabled else 0,
                "output_usd_per_million": 1 if self.enabled else 0}

    def can_reserve(self, provider, input_tokens, output_tokens):
        return self.enabled


class ModelRoutingServiceTests(unittest.TestCase):
    def _setup(self, *, mode="automatic", budget=False, providers=None):
        local = FakeProvider("ollama", "qwen-small")
        gemini = FakeProvider("gemini", "flash")
        providers = providers or {"ollama/qwen-small": local, "gemini/flash": gemini}
        candidates = [
            {"provider": "ollama", "model": "qwen-small", "context_window": 4096,
             "reasoning_score": 0,
             "capabilities": {"chat": True, "streaming": True, "research": True}},
            {"provider": "gemini", "model": "flash", "context_window": 32768,
             "reasoning_score": 3,
             "capabilities": {"chat": True, "streaming": True, "research": True}},
        ]
        env = {"NEXUS_ROUTING_MODE": mode, "NEXUS_ROUTER_CANDIDATES": json.dumps(candidates),
               "NEXUS_ENABLE_REMOTE_PROVIDER": "true", "NEXUS_REMOTE_PROVIDERS": "gemini",
               "NEXUS_TAVILY_ENABLED": "true", "TAVILY_API_KEY": "test-only"}
        manager = FakeManager(env, providers, {
            "ollama": [{"id": "qwen-small", "context_window": 4096,
                        "capabilities": {"chat": True, "streaming": True}}],
            "gemini": [{"id": "flash", "context_window": 32768,
                        "capabilities": {"chat": True, "streaming": True}}],
        })
        budget = FakeBudget(budget)
        return env, manager, ModelRoutingService(manager, budget, router=ModelRouter())

    def test_manual_mode_preserves_selected_provider_without_discovery(self):
        _, manager, service = self._setup(mode="manual")
        result = service.resolve("Explique isso", [{"role": "user", "content": "Explique isso"}])
        self.assertEqual(result.provider.model, "qwen-small")
        self.assertEqual(result.mode, "manual")
        self.assertEqual(manager.checked, [])

    def test_automatic_mode_routes_simple_task_to_local_model(self):
        _, manager, service = self._setup()
        result = service.resolve("Oi", [{"role": "user", "content": "Oi"}])
        self.assertEqual((result.route.provider, result.route.model), ("ollama", "qwen-small"))
        self.assertEqual(result.mode, "automatic")
        self.assertEqual(manager.checked, ["ollama", "gemini"])

    def test_advanced_task_uses_remote_only_with_budget(self):
        _, _, blocked = self._setup()
        with self.assertRaises(NoRouteAvailable):
            blocked.resolve("Compare as alternativas e avalie riscos", [
                {"role": "user", "content": "Compare as alternativas e avalie riscos"}])
        _, _, enabled = self._setup(budget=True)
        result = enabled.resolve("Compare as alternativas e avalie riscos", [
            {"role": "user", "content": "Compare as alternativas e avalie riscos"}])
        self.assertEqual((result.route.provider, result.route.model), ("gemini", "flash"))

    def test_free_quota_routing_never_falls_back_to_paid_provider(self):
        class CountingProvider(FakeProvider):
            def __init__(self, name, model, *, fail=False):
                super().__init__(name, model, fail=fail)
                self.calls = 0

            def generate(self, messages, **kwargs):
                self.calls += 1
                return super().generate(messages, **kwargs)

        gemini = CountingProvider("gemini", "gemini-2.5-flash", fail=True)
        paid = CountingProvider("openai", "gpt-test")
        env = {"NEXUS_ROUTING_MODE": "automatic",
               "NEXUS_ROUTER_CANDIDATES": json.dumps([
                   {"provider": "gemini", "model": "gemini-2.5-flash",
                    "context_window": 32768, "reasoning_score": 2,
                    "capabilities": {"chat": True}},
                   {"provider": "openai", "model": "gpt-test",
                    "context_window": 32768, "reasoning_score": 4,
                    "capabilities": {"chat": True}}]),
               "NEXUS_ENABLE_REMOTE_PROVIDER": "true",
               "NEXUS_REMOTE_PROVIDERS": "gemini,openai"}

        class Manager:
            def __init__(self): self.env = env
            def build(self, name, model):
                return {"gemini": gemini, "openai": paid}[name]
            def list_models(self, name):
                model = "gemini-2.5-flash" if name == "gemini" else "gpt-test"
                return [{"id": model, "context_window": 32768}]
            def check(self, name): return {"available": True}
            def _remote_enabled(self, name): return True
            def selected(self): return gemini

        class FreeQuotaBudget(FakeBudget):
            def settings(self):
                return {"enabled": True, "mode": "free_quota",
                        "input_usd_per_million": 0, "output_usd_per_million": 0}
            def can_reserve(self, provider, input_tokens, output_tokens):
                return (getattr(provider, "provider_name", "") == "gemini"
                        and getattr(provider, "model", "") == "gemini-2.5-flash")

        service = ModelRoutingService(Manager(), FreeQuotaBudget(enabled=True),
                                      wrap_provider=lambda provider: provider)
        result = service.resolve("Oi", [{"role": "user", "content": "Oi"}])
        self.assertEqual((result.route.provider, result.route.model),
                         ("gemini", "gemini-2.5-flash"))
        with self.assertRaises(ProviderUnavailableError):
            result.provider.generate([{"role": "user", "content": "Oi"}])
        self.assertEqual((gemini.calls, paid.calls), (1, 0))

    def test_automatic_router_can_select_openai_when_allowlisted_and_budgeted(self):
        local = FakeProvider("ollama", "qwen-small")
        remote = FakeProvider("openai", "gpt-test")
        candidates = [
            {"provider": "ollama", "model": "qwen-small", "context_window": 4096,
             "reasoning_score": 0, "capabilities": {"chat": True}},
            {"provider": "openai", "model": "gpt-test", "context_window": 32768,
             "reasoning_score": 4, "capabilities": {"chat": True}},
        ]
        env = {"NEXUS_ROUTING_MODE": "automatic",
               "NEXUS_ROUTER_CANDIDATES": json.dumps(candidates),
               "NEXUS_ENABLE_REMOTE_PROVIDER": "true",
               "NEXUS_REMOTE_PROVIDERS": "openai"}
        manager = FakeManager(env, {"ollama/qwen-small": local, "openai/gpt-test": remote}, {
            "ollama": [{"id": "qwen-small", "context_window": 4096,
                        "capabilities": {"chat": True}}],
            "openai": [{"id": "gpt-test", "context_window": 32768,
                        "capabilities": {"chat": True}}],
        })
        service = ModelRoutingService(manager, FakeBudget(enabled=True), router=ModelRouter())
        prompt = "Compare as alternativas e avalie riscos"
        result = service.resolve(prompt, [{"role": "user", "content": prompt}])
        self.assertEqual((result.route.provider, result.route.model), ("openai", "gpt-test"))

    def test_model_unavailable_in_live_catalog_is_never_selected(self):
        _, manager, service = self._setup()
        manager.models["ollama"] = []
        with self.assertRaises(NoRouteAvailable):
            service.resolve("Oi", [{"role": "user", "content": "Oi"}])

    def test_resolved_fallback_chain_stays_local_and_retries_transient_error(self):
        failing = FakeProvider("ollama", "qwen-small", fail=True)
        alternate = FakeProvider("ollama", "qwen-alt")
        env = {"NEXUS_ROUTING_MODE": "automatic",
               "NEXUS_ROUTER_CANDIDATES": json.dumps([
                   {"provider": "ollama", "model": "qwen-small", "context_window": 4096,
                    "reasoning_score": 0, "latency_ms": 1,
                    "capabilities": {"chat": True}},
                   {"provider": "ollama", "model": "qwen-alt", "context_window": 4096,
                    "reasoning_score": 0, "latency_ms": 5,
                    "capabilities": {"chat": True}}])}

        class Manager:
            def __init__(self): self.env=env
            def build(self, name, model): return {"qwen-small": failing, "qwen-alt": alternate}[model]
            def list_models(self, name):
                return [{"id": "qwen-small", "context_window": 4096},
                        {"id": "qwen-alt", "context_window": 4096}]
            def check(self, name): return {"available": True}
            def selected(self): return failing
            def _remote_enabled(self, name): return False

        result=ModelRoutingService(Manager(),FakeBudget()).resolve(
            "Oi",[{"role":"user","content":"Oi"}])
        response=result.provider.generate([{"role":"user","content":"Oi"}])
        self.assertEqual((response.provider,response.model),("ollama","qwen-alt"))


class FallbackProviderTests(unittest.TestCase):
    def test_retries_transient_failure_and_returns_actual_provider_metadata(self):
        failing = FakeProvider("ollama", "broken", fail=True)
        alternate = FakeProvider("ollama", "healthy")
        chain = FallbackProvider([failing, alternate])
        response = chain.generate([{"role": "user", "content": "hi"}])
        self.assertEqual((response.provider, response.model), ("ollama", "healthy"))

    def test_stream_fallback_only_before_first_chunk(self):
        before = FallbackProvider([FakeProvider("ollama", "broken", fail=True),
                                   FakeProvider("ollama", "healthy")])
        self.assertEqual(list(before.stream_generate([])), ["ok"])

        class PartialFailure(FakeProvider):
            def stream_generate(self, messages, **kwargs):
                yield "partial"
                raise ProviderUnavailableError()

        partial = FallbackProvider([PartialFailure("ollama", "partial"),
                                    FakeProvider("ollama", "alternate")])
        iterator = partial.stream_generate([])
        self.assertEqual(next(iterator), "partial")
        with self.assertRaises(ProviderUnavailableError):
            next(iterator)


if __name__ == "__main__":
    unittest.main()
