import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from nexus_learning.engine import LearningEngine
from nexus_learning.providers.errors import ProviderConfigurationError, ProviderModelNotFoundError
from nexus_learning.providers.manager import ProviderManager
from nexus_learning.providers.ollama import OllamaProvider


class FakeResponse:
    def __init__(self, payload=None, lines=None):
        self.payload = json.dumps(payload or {}).encode()
        self.lines = lines or []
        self.closed = False

    def __enter__(self): return self
    def __exit__(self, *_): self.close()
    def read(self, _limit=-1): return self.payload
    def __iter__(self): return iter(self.lines)
    def close(self): self.closed = True


class FakeOpener:
    def __init__(self, *responses): self.responses, self.requests = list(responses), []
    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        return self.responses.pop(0)


class NotFoundOpener:
    def __call__(self, request, timeout):
        raise HTTPError(request.full_url, 404, "not found", {}, io.BytesIO())


class OllamaProviderTests(unittest.TestCase):
    def test_loopback_only_and_bounded_resource_settings(self):
        with self.assertRaises(ProviderConfigurationError):
            OllamaProvider("http://example.com:11434", "qwen:small")
        with self.assertRaises(ProviderConfigurationError):
            OllamaProvider(num_ctx=65536)

    def test_connection_discovery_generation_and_history_payload(self):
        opener = FakeOpener(
            FakeResponse({"version": "0.40.13"}),
            FakeResponse({"models": [{"name": "qwen2.5:0.5b"}]}),
            FakeResponse({"models": [{"name": "qwen2.5:0.5b", "size": 397821319}]}),
            FakeResponse({"model": "qwen2.5:0.5b", "message": {"content": "Olá."},
                          "prompt_eval_count": 16, "eval_count": 3}),
        )
        provider = OllamaProvider(model="qwen2.5:0.5b", num_ctx=1024,
                                  num_predict=24, opener=opener)
        self.assertTrue(provider.check_connection()["available"])
        models = provider.list_models()
        self.assertEqual(models[0]["id"], "qwen2.5:0.5b")
        result = provider.generate([{"role": "user", "content": "Oi"},
                                    {"role": "assistant", "content": "Olá"},
                                    {"role": "user", "content": "Como vai?"}], timeout=25)
        self.assertEqual(result.text, "Olá.")
        sent = json.loads(opener.requests[-1][0].data)
        self.assertEqual(sent["messages"][1]["role"], "assistant")
        self.assertEqual(sent["options"], {"num_ctx": 1024, "num_predict": 24,
                                           "temperature": 0.2})
        self.assertEqual(opener.requests[-1][1], 25)

    def test_streaming_yields_deltas_and_closes_response(self):
        response = FakeResponse(lines=[
            (json.dumps({"message": {"content": "Olá"}, "done": False}) + "\n").encode(),
            (json.dumps({"message": {"content": " mundo"}, "done": True}) + "\n").encode(),
        ])
        provider = OllamaProvider(model="qwen2.5:0.5b", opener=FakeOpener(response))
        self.assertEqual(list(provider.stream_generate([{"role": "user", "content": "Oi"}])),
                         ["Olá", " mundo"])
        self.assertTrue(response.closed)

    def test_unknown_model_is_not_downloaded_or_replaced(self):
        provider = OllamaProvider(model="qwen3:large", opener=NotFoundOpener())
        with self.assertRaises(ProviderModelNotFoundError):
            provider.generate([{"role": "user", "content": "Oi"}])


class ProviderManagerTests(unittest.TestCase):
    def test_manual_gemini_and_openai_selection_uses_allowlisted_adapters_without_leaking_keys(self):
        class CatalogAdapter:
            provider_name = "catalog"
            model = None
            def __init__(self, api_key, model=None, **kwargs):
                self.received_key = api_key
                self.model = model
                self.provider_name = "gemini" if kwargs.get("embedding_model") else "openai"
            def list_models(self):
                return [{"id": "gemini-test" if self.provider_name == "gemini" else "gpt-test"}]
            def check_connection(self):
                return {"provider": self.provider_name, "available": True, "model_count": 1}

        engine=LearningEngine(":memory:")
        try:
            env={"NEXUS_ENABLE_REMOTE_PROVIDER":"true",
                 "NEXUS_REMOTE_PROVIDERS":"gemini,openai",
                 "GEMINI_API_KEY":"gemini-test-secret","GEMINI_MODEL":"gemini-test",
                 "OPENAI_API_KEY":"openai-test-secret","OPENAI_MODEL":"gpt-test"}
            manager=ProviderManager(engine,env)
            with patch("nexus_learning.providers.manager.GeminiProvider",CatalogAdapter), \
                 patch("nexus_learning.providers.manager.OpenAIProvider",CatalogAdapter):
                for provider, model in (("gemini","gemini-test"),("openai","gpt-test")):
                    self.assertEqual(manager.select(provider,model),{"provider":provider,"model":model})
                    selected=manager.selected()
                    self.assertEqual((selected.provider_name,selected.model),(provider,model))
                status=json.dumps(manager.status())
                self.assertNotIn("test-secret",status)
            self.assertEqual(manager.default(),{"provider":"openai","model":"gpt-test"})
        finally:
            engine.close()

    def test_remote_provider_allowlist_prevents_unselected_environment_keys(self):
        engine=LearningEngine(":memory:")
        try:
            manager=ProviderManager(engine,{"NEXUS_ENABLE_REMOTE_PROVIDER":"true",
                "NEXUS_REMOTE_PROVIDERS":"gemini","GEMINI_API_KEY":"fake",
                "GEMINI_MODEL":"gemini-test","OPENAI_API_KEY":"unused-existing-key",
                "OPENAI_MODEL":"unused-model"})
            self.assertEqual(manager.build("gemini").provider_name,"gemini")
            with self.assertRaises(ProviderConfigurationError): manager.build("openai")
            state={row["id"]:row for row in manager.status()["providers"]}
            self.assertTrue(state["gemini"]["enabled"])
            self.assertFalse(state["openai"]["enabled"])
        finally: engine.close()

    def test_selects_discovered_qwen_and_persists_selection(self):
        engine = LearningEngine(":memory:")
        try:
            manager = ProviderManager(engine, {"NEXUS_PROVIDER": "ollama",
                "OLLAMA_MODEL": "qwen2.5:0.5b", "OLLAMA_BASE_URL": "http://127.0.0.1:11434"})
            manager.list_models = lambda _name: [{"id": "qwen2.5:0.5b"}]
            selected = manager.select("ollama", "qwen2.5:0.5b")
            self.assertEqual(selected, {"provider": "ollama", "model": "qwen2.5:0.5b"})
            self.assertEqual(manager.default(), selected)
        finally:
            engine.close()

    def test_mock_requires_explicit_development_configuration_and_is_never_remote(self):
        engine = LearningEngine(":memory:")
        try:
            manager = ProviderManager(engine, {"NEXUS_PROVIDER": "mock", "NEXUS_ENVIRONMENT": "development"})
            provider = manager.selected()
            self.assertEqual(provider.provider_name, "mock")
            self.assertEqual(provider.generate([{"role": "user", "content": "Hi"}]).provider, "mock")
            self.assertFalse(manager.check("mock")["available"])
        finally:
            engine.close()


if __name__ == "__main__":
    unittest.main()
