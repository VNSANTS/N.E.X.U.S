import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from wsgiref.simple_server import make_server

from nexus_learning.api import NexusAPI
from nexus_learning.engine import LearningEngine


class APIHTTPTests(unittest.TestCase):
    def setUp(self):
        self.engine = LearningEngine(":memory:")
        self.app = NexusAPI(self.engine)
        self.app.auth.create_user("local", "safe test password 12345")
        self.server = make_server("127.0.0.1", 0, self.app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.engine.close()

    def request(self, path, method="GET", body=None, token=None):
        payload = None if body is None else json.dumps(body).encode()
        headers = {}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = "Bearer " + token
        req = Request(self.base + path, data=payload, headers=headers, method=method)
        with urlopen(req, timeout=5) as response:
            raw = response.read()
            content_type = response.headers.get("Content-Type", "")
        return json.loads(raw) if "application/json" in content_type else raw

    def test_http_ui_login_and_authenticated_sessions(self):
        page = self.request("/")
        self.assertIn(b"N.E.X.U.S.", page)
        ui = page.decode("utf-8")
        self.assertIn('data-view="dashboard"', ui)
        self.assertIn('data-view="learning"', ui)
        self.assertIn('data-view="integrations"', ui)
        self.assertIn("Pesquisas e fontes", ui)
        self.assertNotIn("Ã£", ui)
        self.assertNotIn("\ufffd", ui)
        login = self.request("/api/v1/auth/login", "POST",
                             {"username": "local", "password": "safe test password 12345"})
        session = self.request("/api/v1/sessions", "POST", {}, login["access_token"])
        self.assertTrue(session["id"].startswith("ses_"))
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/v1/sessions")
        self.assertEqual(caught.exception.code, 401)

    def test_provider_catalog_and_secret_safe_status(self):
        login = self.request("/api/v1/auth/login", "POST",
                             {"username": "local", "password": "safe test password 12345"})
        token = login["access_token"]
        providers = self.request("/api/v1/providers", token=token)
        ids = {item["id"] for item in providers["providers"]}
        self.assertTrue({"ollama", "openai", "anthropic", "gemini", "openrouter"}.issubset(ids))
        self.assertNotIn("api_key", json.dumps(providers).lower())
        models = self.request("/api/v1/providers/mock/models", token=token)
        self.assertEqual(models["models"][0]["id"], "offline-mock")

    def test_authenticated_streaming_chat_persists_real_provider_metadata_and_history(self):
        from nexus_learning.providers.manager import ProviderManager

        class StreamingTestProvider:
            provider_name = "mock"
            model = "stream-test"

            def stream_generate(self, messages, **kwargs):
                self.messages = messages
                yield "Resposta "
                yield "real em stream."

        self.app.provider_manager = ProviderManager(self.engine, {},
                                                     injected_provider=StreamingTestProvider())
        self.app.model_routing.manager = self.app.provider_manager
        login = self.request("/api/v1/auth/login", "POST",
                             {"username": "local", "password": "safe test password 12345"})
        token = login["access_token"]
        session = self.request("/api/v1/sessions", "POST", {"title": "stream"}, token)
        request = Request(self.base + f"/api/v1/sessions/{session['id']}/messages/stream",
                          data=json.dumps({"content": "Explique o fluxo."}).encode(),
                          headers={"Content-Type": "application/json", "Authorization": "Bearer " + token},
                          method="POST")
        with urlopen(request, timeout=5) as response:
            self.assertEqual(response.headers.get_content_type(), "text/event-stream")
            stream = response.read().decode("utf-8")
        self.assertIn('event: delta', stream)
        self.assertIn('"text":"Resposta "', stream)
        self.assertIn('"model":"stream-test"', stream)
        history = self.request(f"/api/v1/sessions/{session['id']}/messages", token=token)
        self.assertEqual([row["role"] for row in history], ["user", "assistant"])
        self.assertEqual(history[-1]["content"], "Resposta real em stream.")

    def test_automatic_model_routing_is_used_by_real_http_stream_and_audited(self):
        from nexus_learning.routing import ModelRoutingService

        class LocalProvider:
            provider_name = "ollama"
            model = "qwen-small"
            def stream_generate(self, messages, **kwargs):
                yield "Rota automatica funcional."

        provider = LocalProvider()
        env = {"NEXUS_ROUTING_MODE": "automatic",
               "NEXUS_ROUTER_CANDIDATES": json.dumps([{
                   "provider": "ollama", "model": "qwen-small", "context_window": 4096,
                   "reasoning_score": 0, "capabilities": {"chat": True, "streaming": True}}]),
               "OLLAMA_NUM_CTX": "4096"}

        class Manager:
            def __init__(self): self.env = env
            def selected(self): return provider
            def build(self, name, model): return provider
            def list_models(self, name):
                return [{"id": "qwen-small", "context_window": 4096,
                         "capabilities": {"chat": True, "streaming": True}}]
            def check(self, name): return {"available": True}
            def _remote_enabled(self, name): return False

        manager = Manager()
        self.app.provider_manager = manager
        self.app.model_routing = ModelRoutingService(
            manager, self.app.provider_budget, env=env, wrap_provider=self.app._wrap_provider)
        login = self.request("/api/v1/auth/login", "POST",
                             {"username": "local", "password": "safe test password 12345"})
        token = login["access_token"]
        session = self.request("/api/v1/sessions", "POST", {}, token)
        request = Request(self.base + f"/api/v1/sessions/{session['id']}/messages/stream",
                          data=json.dumps({"content": "Oi"}).encode(),
                          headers={"Content-Type": "application/json", "Authorization": "Bearer " + token},
                          method="POST")
        with urlopen(request, timeout=5) as response:
            stream = response.read().decode("utf-8")
        self.assertIn('"routing_mode":"automatic"', stream)
        self.assertIn('"tier":"SIMPLE"', stream)
        self.assertIn('"model":"qwen-small"', stream)
        activity = self.request("/api/v1/activity", token=token)
        self.assertTrue(any(item["event"] == "model.routed" for item in activity))
        self.assertTrue(any(item["event"] == "model.completed" for item in activity))


if __name__ == "__main__":
    unittest.main()
