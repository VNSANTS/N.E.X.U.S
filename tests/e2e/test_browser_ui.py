"""Opt-in Playwright E2E tests.

Run with:
    python -m pip install -r requirements-e2e.txt
    python -m playwright install chromium
    python -m unittest discover -s tests/e2e -v

The fixture uses an in-memory SQLite database and an injected deterministic
provider. It binds only to an ephemeral 127.0.0.1 port and makes no external
provider or research calls. Without the optional dependency/browser, tests are
reported as skipped rather than failing unrelated unit-test discovery.
"""
import threading
import unittest
import json
import os
from wsgiref.simple_server import WSGIRequestHandler, make_server
from unittest.mock import patch

from nexus_learning.api import NexusAPI
from nexus_learning.engine import LearningEngine

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import expect, sync_playwright
except ImportError:  # Playwright is an explicit opt-in test dependency.
    PlaywrightError = None
    expect = None
    sync_playwright = None


class BrowserStreamProvider:
    provider_name = "mock"
    model = "e2e-deterministic"

    def __init__(self):
        self.specialist_calls = 0

    def generate(self, messages, **kwargs):
        from nexus_learning.providers.base import ModelResponse
        agent = ("architect", "analyst", "reviewer")[self.specialist_calls]
        self.specialist_calls += 1
        return ModelResponse(json.dumps({"summary": agent + " plan", "items": [], "claims": []}),
                             self.provider_name, self.model)

    def stream_generate(self, messages, **kwargs):
        yield "Resposta "
        yield "persistida pelo navegador."


class QuietRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


@unittest.skipIf(sync_playwright is None, "install optional requirements-e2e.txt")
class BrowserUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch(headless=True)
        except PlaywrightError as exc:
            cls.playwright.stop()
            raise unittest.SkipTest(
                "Playwright Chromium is unavailable; run `python -m playwright install chromium`"
            ) from exc

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.engine = LearningEngine(":memory:")
        self.app = NexusAPI(self.engine, provider=BrowserStreamProvider())
        self.app.auth.create_user("browser-owner", "browser e2e password 12345")
        self.server = make_server("127.0.0.1", 0, self.app,
                                  handler_class=QuietRequestHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self.context = self.browser.new_context(viewport={"width": 1280, "height": 900})
        self.page = self.context.new_page()
        self.page_errors = []
        self.page.on("pageerror", lambda error: self.page_errors.append(str(error)))
        self.page.goto(f"http://127.0.0.1:{self.server.server_port}/", wait_until="networkidle")

    def tearDown(self):
        self.context.close()
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join(timeout=3)
        self.engine.close()

    def login(self):
        self.page.locator('#loginForm [name="username"]').fill("browser-owner")
        self.page.locator('#loginForm [name="password"]').fill("browser e2e password 12345")
        self.page.locator('#loginForm button[type="submit"], #loginForm button').click()
        expect(self.page.locator("#login")).to_be_hidden()
        expect(self.page.locator("#viewTitle")).to_have_text("Dashboard")

    def test_authentication_and_primary_navigation(self):
        form = self.page.locator("#loginForm")
        form.locator('[name="username"]').fill("browser-owner")
        form.locator('[name="password"]').fill("wrong password")
        form.locator("button").click()
        expect(self.page.locator("#loginError")).to_contain_text("invalid credentials")
        self.login()

        views = {
            "learning": "Aprendizagem",
            "research": "Pesquisas e fontes",
            "memories": "Memórias",
            "claims": "Conhecimento",
            "agents": "Agentes",
            "tasks": "Tarefas",
            "jobs": "Fila do worker",
            "activity": "Atividade",
            "providers": "Provedores",
            "integrations": "Integrações",
            "tools": "Ferramentas",
            "settings": "Configurações",
        }
        for view, title in views.items():
            with self.subTest(view=view):
                self.page.locator(f'[data-view="{view}"]').click()
                expect(self.page.locator("#viewTitle")).to_have_text(title)
                expect(self.page.locator("#content .loading")).to_be_hidden()
                expect(self.page.locator("#content .error-box")).to_have_count(0)
        self.assertEqual(self.page_errors, [])

    def test_streaming_history_new_conversation_and_relogin(self):
        self.login()
        self.page.locator('[data-view="conversation"]').click()
        expect(self.page.locator("#conversation")).to_be_visible()
        self.page.locator("#input").fill("Teste E2E do fluxo de conversa")
        self.page.locator("#sendButton").click()

        expect(self.page.locator("#messages .message.assistant .message-content")).to_contain_text(
            "Resposta persistida pelo navegador.", timeout=10000
        )
        expect(self.page.locator("#messages .message-label").filter(
            has_text="mock / e2e-deterministic")).to_be_visible()
        expect(self.page.locator("#sessions .session-item")).to_have_count(1)

        self.page.locator("#newSession").click()
        expect(self.page.locator("#messages .welcome")).to_be_visible()
        expect(self.page.locator("#sessions .session-item")).to_have_count(2)
        self.page.locator("#sessions .session-item").nth(1).click()
        expect(self.page.locator("#messages .message.user .message-content")).to_have_text(
            "Teste E2E do fluxo de conversa"
        )
        expect(self.page.locator("#messages .message.assistant .message-content")).to_have_text(
            "Resposta persistida pelo navegador."
        )

        self.page.locator("#logout").click()
        expect(self.page.locator("#login")).to_be_visible()
        self.page.reload(wait_until="networkidle")
        expect(self.page.locator("#login")).to_be_visible()
        self.login()
        self.assertEqual(self.page_errors, [])

    def test_opt_in_specialist_pipeline_reaches_browser_stream(self):
        self.login()
        self.page.locator('[data-view="conversation"]').click()
        with patch.dict(os.environ, {"NEXUS_MULTIAGENT_ENABLED": "true"}):
            self.page.locator("#input").fill("Analise e planeje um fluxo de trabalho")
            self.page.locator("#sendButton").click()
            expect(self.page.locator("#messages .message.assistant .message-content")).to_contain_text(
                "Resposta persistida pelo navegador.", timeout=10000
            )
        provider = self.app.provider_manager.injected_provider
        self.assertEqual(provider.specialist_calls, 3)
        with self.engine.db() as connection:
            events = [row[0] for row in connection.execute(
                "SELECT event FROM api_activity WHERE event LIKE 'agent.llm_call_%'").fetchall()]
        self.assertEqual(events.count("agent.llm_call_started"), 3)
        self.assertEqual(events.count("agent.llm_call_completed"), 3)
        self.assertEqual(self.page_errors, [])

    def test_mobile_sidebar_opens_and_closes_after_navigation(self):
        self.login()
        self.page.set_viewport_size({"width": 390, "height": 844})
        menu = self.page.locator("#mobileMenu")
        expect(menu).to_be_visible()
        menu.click()
        expect(self.page.locator("#sidebar")).to_have_class("sidebar open")
        self.page.locator('[data-view="learning"]').click()
        expect(self.page.locator("#viewTitle")).to_have_text("Aprendizagem")
        expect(self.page.locator("#sidebar")).to_have_class("sidebar")
        self.assertEqual(self.page_errors, [])

    def test_learning_topic_cycle_and_external_research_confirmation(self):
        self.login()
        self.page.locator('[data-view="learning"]').click()
        expect(self.page.locator("#content .error-box")).to_have_count(0)

        self.page.get_by_placeholder("Adicionar assunto").fill("browser cycle topic")
        self.page.get_by_role("button", name="Adicionar", exact=True).click()
        expect(self.page.locator("#content")).to_contain_text("browser cycle topic")
        self.page.get_by_role("button", name="Iniciar ciclo").click()
        expect(self.page.locator("#content")).to_contain_text("observe · running")

        self.page.get_by_placeholder("Adicionar assunto").fill("external research must be declined")
        self.page.locator("#content input[type=checkbox]").check()
        self.page.once("dialog", lambda dialog: dialog.dismiss())
        self.page.get_by_role("button", name="Adicionar", exact=True).click()
        expect(self.page.locator("#content")).not_to_contain_text(
            "external research must be declined"
        )
        self.assertEqual(self.page_errors, [])


if __name__ == "__main__":
    unittest.main()
