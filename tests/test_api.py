"""Integration coverage for the local authenticated API."""
import io
import json
import unittest

from nexus_learning.api import NexusAPI
from nexus_learning.engine import LearningEngine


class RecordingProvider:
    def __init__(self):
        self.messages = None
        self.response = "Resposta simulada e controlada."
        self.provider_name = "mock"
        self.model = "recording"

    def generate(self, messages, *, max_tokens=800, timeout=30):
        from nexus_learning.providers.base import ModelResponse
        self.messages = messages
        return ModelResponse(self.response, "test", "recording")

    def stream_generate(self, messages, *, max_tokens=800, timeout=30, cancel_event=None):
        self.messages = messages
        yield self.response


class SpecialistAwareProvider(RecordingProvider):
    provider_name = "ollama"

    def __init__(self):
        super().__init__()
        self.calls = []

    def generate(self, messages, *, max_tokens=800, timeout=30, task_id=None):
        from nexus_learning.providers.base import ModelResponse
        self.calls.append(messages)
        self.messages = messages
        if len(self.calls) <= 3:
            import json
            agent = ("architect", "analyst", "reviewer")[len(self.calls) - 1]
            return ModelResponse(json.dumps({"summary": agent + " result", "items": [], "claims": []}),
                                 self.provider_name, self.model)
        return ModelResponse(self.response, self.provider_name, self.model)

    def stream_generate(self, messages, *, max_tokens=800, timeout=30, cancel_event=None):
        self.messages = messages
        yield self.response


class APITests(unittest.TestCase):
    def setUp(self):
        self.engine = LearningEngine(":memory:")
        self.provider = RecordingProvider()
        self.app = NexusAPI(self.engine, self.provider)
        self.app.auth.create_user("owner", "correct horse battery staple")
        self.owner = self.app.auth.login("owner", "correct horse battery staple")["access_token"]

    def tearDown(self):
        self.engine.close()

    def request(self, path, method="GET", body=None, token=None, host="127.0.0.1", query=""):
        raw = b"" if body is None else json.dumps(body).encode()
        environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
                   "CONTENT_LENGTH": str(len(raw)), "CONTENT_TYPE": "application/json",
                   "wsgi.input": io.BytesIO(raw), "HTTP_HOST": host,
                   "HTTP_AUTHORIZATION": "Bearer " + token if token else "",
                   "SERVER_NAME": "127.0.0.1", "SERVER_PORT": "8765", "wsgi.url_scheme": "http"}
        captured = {}
        def start(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)
        payload = b"".join(self.app(environ, start))
        captured["body"] = json.loads(payload) if captured["headers"].get("Content-Type", "").startswith("application/json") else payload
        return captured

    def test_authentication_host_guard_and_session_isolation(self):
        self.assertTrue(self.request("/api/v1/sessions")["status"].startswith("401"))
        self.assertTrue(self.request("/api/v1/health", host="evil.example")["status"].startswith("403"))
        created = self.request("/api/v1/sessions", "POST", {"title": "private"}, self.owner)
        self.assertTrue(created["status"].startswith("201"))
        session_id = created["body"]["id"]
        hidden = self.request(f"/api/v1/sessions/non-owned/messages", token=self.owner)
        self.assertTrue(hidden["status"].startswith("404"))
        self.assertFalse(self.app._owns_session(session_id, "another-user"))
        self.assertEqual(self.request("/api/v1/auth/me", token=self.owner)["body"]["username"], "owner")

    def _free_gemini_app(self):
        class GeminiSimulator:
            provider_name = "gemini"
            model = "gemini-2.5-flash"

            def __init__(self):
                self.calls = []

            def generate(self, messages, *, max_tokens=800, timeout=30):
                from nexus_learning.providers.base import ModelResponse
                self.calls.append(("generate", messages))
                return ModelResponse("Resposta Gemini simulada.", self.provider_name,
                                     self.model, input_tokens=20, output_tokens=5)

            def stream_generate(self, messages, *, max_tokens=800, timeout=60,
                                cancel_event=None):
                self.calls.append(("stream", messages))
                yield "Resposta "
                yield "Gemini simulada."

        engine = LearningEngine(":memory:")
        provider = GeminiSimulator()
        app = NexusAPI(engine, provider)
        app.auth.create_user("owner", "correct horse battery staple")
        token = app.auth.login("owner", "correct horse battery staple")["access_token"]
        budget = self._request_for_app(app, "/api/v1/usage/budget", "POST", {
            "confirm": True, "enabled": True, "mode": "free_quota",
            "daily_calls": 10, "daily_tokens": 5000, "daily_usd": 0,
            "task_calls": 5, "task_tokens": 5000, "task_usd": 0,
            "input_usd_per_million": 0, "output_usd_per_million": 0}, token)
        if not budget["status"].startswith("200"):
            engine.close()
            self.fail(f"could not configure simulated free quota: {budget}")
        response = self._request_for_app(app, "/api/v1/sessions", "POST", {}, token)
        session_id = response["body"]["id"]
        return engine, provider, app, token, session_id

    @staticmethod
    def _request_for_app(app, path, method, body, token):
        raw = json.dumps(body).encode()
        environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": "",
                   "CONTENT_LENGTH": str(len(raw)), "CONTENT_TYPE": "application/json",
                   "wsgi.input": io.BytesIO(raw), "HTTP_HOST": "127.0.0.1",
                   "HTTP_AUTHORIZATION": "Bearer " + token,
                   "SERVER_NAME": "127.0.0.1", "SERVER_PORT": "8765", "wsgi.url_scheme": "http"}
        captured = {}
        def start(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)
        payload = b"".join(app(environ, start))
        captured["body"] = (json.loads(payload) if
            captured["headers"].get("Content-Type", "").startswith("application/json") else payload)
        return captured

    def test_free_quota_chat_sends_authenticated_message_to_gemini_simulator(self):
        engine, provider, app, token, session_id = self._free_gemini_app()
        try:
            response = self._request_for_app(app,
                f"/api/v1/sessions/{session_id}/messages", "POST",
                {"content": "Olá, responda em português."}, token)
            self.assertTrue(response["status"].startswith("200"), response["body"])
            self.assertEqual(response["body"]["message"]["content"], "Resposta Gemini simulada.")
            self.assertEqual(len(provider.calls), 1)
            self.assertEqual(provider.calls[0][0], "generate")
            usage = app.provider_budget.usage()["today"]
            self.assertEqual(usage[0]["provider"], "gemini")
            self.assertEqual(usage[0]["calls"], 1)
        finally:
            engine.close()

    def test_free_quota_stream_sends_message_to_gemini_simulator(self):
        engine, provider, app, token, session_id = self._free_gemini_app()
        try:
            response = self._request_for_app(app,
                f"/api/v1/sessions/{session_id}/messages/stream", "POST",
                {"content": "Olá, faça streaming."}, token)
            self.assertTrue(response["status"].startswith("200"), response["status"])
            self.assertIn(b"event: done", response["body"])
            self.assertIn("Resposta Gemini simulada.", response["body"].decode())
            self.assertEqual([call[0] for call in provider.calls], ["stream"])
            usage = app.provider_budget.usage()["today"]
            self.assertEqual(usage[0]["calls"], 1)
        finally:
            engine.close()

    def test_chat_persists_messages_task_and_retrieves_only_eligible_memory(self):
        sid = self.request("/api/v1/sessions", "POST", {}, self.owner)["body"]["id"]
        memory_id = self.engine.add_memory("episodic", "Projeto ponte", "A ponte azul usa aÃ§o especial.")
        source_id = self.engine.add_source("https://example.invalid/bridge", "Bridge source")
        claim_id = self.engine.propose_claim("A ponte fica sobre o rio", [source_id],
                                             {source_id: "Trecho de evidÃªncia sobre a ponte"})
        self.engine.review_claim(claim_id, "validated", "Revisado com fonte", .92)
        proposed_id = self.engine.propose_claim("A ponte proposta Ã© vermelha", [source_id])
        reply = self.request(f"/api/v1/sessions/{sid}/messages", "POST",
                             {"content": "Me conte sobre a ponte azul"}, self.owner)
        self.assertTrue(reply["status"].startswith("200"), reply["body"])
        context = "\n".join(m["content"] for m in self.provider.messages)
        self.assertIn(memory_id, context)
        self.assertIn(claim_id, context)
        self.assertNotIn(proposed_id, context)
        history = self.request(f"/api/v1/sessions/{sid}/messages", token=self.owner)["body"]
        self.assertEqual([m["role"] for m in history], ["user", "assistant"])
        self.assertTrue(history[0]["task_id"])
        task = self.request("/api/v1/tasks/" + history[0]["task_id"], token=self.owner)
        self.assertEqual(task["body"]["state"], "completed")
        self.assertEqual(self.request("/api/v1/tasks", token=self.owner)["body"][0]["id"], history[0]["task_id"])

    def test_chat_loads_only_relevant_owner_approved_skill_on_demand(self):
        draft=self.app.skills.propose("research-brief","1.0.0","Research source evidence",
                                       "Compare sources and mark uncertainty.")
        sid=self.request("/api/v1/sessions","POST",{},self.owner)["body"]["id"]
        before=self.request(f"/api/v1/sessions/{sid}/messages","POST",
                            {"content":"Research source evidence"},self.owner)
        self.assertTrue(before["status"].startswith("200"))
        self.assertNotIn("Compare sources",json.dumps(self.provider.messages))
        self.app.skills.approve(draft,owner_id="owner",approved=True)
        after=self.request(f"/api/v1/sessions/{sid}/messages","POST",
                           {"content":"Research source evidence"},self.owner)
        self.assertTrue(after["status"].startswith("200"))
        self.assertIn("Compare sources",json.dumps(self.provider.messages))
        self.assertTrue(any("untrusted procedural suggestions" in message["content"]
                            for message in self.provider.messages))

    def test_skill_proposals_are_owner_authenticated_and_approved_explicitly(self):
        created = self.request("/api/v1/skills", "POST", {
            "name": "research-brief",
            "version": "1.0.0",
            "description": "Research source evidence",
            "instructions": "Use cited sources and mark uncertainty.",
        }, self.owner)
        self.assertTrue(created["status"].startswith("201"), created)
        skill_id = created["body"]["id"]

        unauthenticated = self.request("/api/v1/skills/proposals")
        self.assertTrue(unauthenticated["status"].startswith("401"))

        proposals = self.request("/api/v1/skills/proposals", token=self.owner)
        self.assertTrue(proposals["status"].startswith("200"), proposals)
        self.assertEqual([row["id"] for row in proposals["body"]], [skill_id])
        self.assertEqual(proposals["body"][0]["instructions"],
                         "Use cited sources and mark uncertainty.")
        self.assertTrue(proposals["body"][0]["integrity_ok"])

        approved = self.request(f"/api/v1/skills/{skill_id}/approve", "POST",
                                {"confirm": True}, self.owner)
        self.assertTrue(approved["status"].startswith("200"), approved)
        self.assertEqual(self.request("/api/v1/skills/proposals", token=self.owner)["body"], [])

    def test_tampered_skill_proposal_is_blocked_by_api_approval(self):
        created = self.request("/api/v1/skills", "POST", {
            "name": "tamper-check",
            "version": "1.0.0",
            "description": "A proposal for integrity testing",
            "instructions": "Original instructions for review.",
        }, self.owner)
        self.assertTrue(created["status"].startswith("201"), created)
        skill_id = created["body"]["id"]
        with self.engine.db() as c:
            c.execute("UPDATE runtime_skills SET instructions=? WHERE id=?",
                      ("Altered after proposal", skill_id))

        proposals = self.request("/api/v1/skills/proposals", token=self.owner)
        self.assertFalse(proposals["body"][0]["integrity_ok"])
        approval = self.request(f"/api/v1/skills/{skill_id}/approve", "POST",
                                {"confirm": True}, self.owner)
        self.assertTrue(approval["status"].startswith("400"), approval)
        remaining = self.request("/api/v1/skills/proposals", token=self.owner)["body"]
        self.assertEqual(remaining[0]["status"], "proposed")
        self.assertFalse(remaining[0]["integrity_ok"])

    def test_skill_proposal_can_be_rejected_only_with_explicit_confirmation(self):
        created = self.request("/api/v1/skills", "POST", {
            "name": "temporary-skill",
            "version": "1.0.0",
            "description": "A temporary proposed skill",
            "instructions": "Draft instructions for owner review.",
        }, self.owner)
        skill_id = created["body"]["id"]
        pending = self.request("/api/v1/skills/proposals", token=self.owner)
        self.assertEqual([row["id"] for row in pending["body"]], [skill_id])

        denied = self.request(f"/api/v1/skills/{skill_id}/reject", "POST",
                              {"confirm": False}, self.owner)
        self.assertTrue(denied["status"].startswith("403"))
        self.assertEqual(len(self.request("/api/v1/skills/proposals", token=self.owner)["body"]), 1)

        rejected = self.request(f"/api/v1/skills/{skill_id}/reject", "POST",
                                {"confirm": True}, self.owner)
        self.assertTrue(rejected["status"].startswith("200"), rejected)
        self.assertEqual(rejected["body"]["status"], "rejected")
        self.assertEqual(self.request("/api/v1/skills/proposals", token=self.owner)["body"], [])
        self.assertEqual(self.request("/api/v1/skills", token=self.owner,
                                         query="query=temporary")["body"], [])

    def test_skill_discovery_endpoint_reads_query_string(self):
        research = self.app.skills.propose(
            "research-brief", "1.0.0", "Research source evidence", "Compare sourced evidence.")
        review = self.app.skills.propose(
            "code-review", "1.0.0", "Review software changes", "Check code regressions.")
        self.app.skills.approve(research, owner_id="owner", approved=True)
        self.app.skills.approve(review, owner_id="owner", approved=True)

        response = self.request("/api/v1/skills", token=self.owner, query="query=research")
        self.assertTrue(response["status"].startswith("200"), response)
        self.assertEqual([item["name"] for item in response["body"]], ["research-brief"])

    def test_chat_executes_allowlisted_model_tool_through_policy_and_returns_result(self):
        import os
        from unittest.mock import patch
        from nexus_learning.providers.base import ModelResponse, ToolCall

        class ToolChatProvider:
            provider_name = "ollama"
            model = "qwen-offline-test"
            supports_tools = True
            def __init__(self): self.calls = []
            def generate(self, messages, *, max_tokens=800, timeout=30, tools=None):
                self.calls.append((messages, tools))
                if len(self.calls) == 1:
                    return ModelResponse("", self.provider_name, self.model,
                        tool_calls=(ToolCall("lookup-1", "memory.search", {"query": "favorite color"}),))
                self.assert_result = messages[-1]["content"]
                return ModelResponse("A memória encontrada diz azul.", self.provider_name, self.model)

        provider = ToolChatProvider()
        self.app = NexusAPI(self.engine, provider)
        with self.engine.db() as c:
            c.execute("UPDATE provider_settings SET provider='ollama',model=? WHERE id=1",
                      (provider.model,))
        self.owner = self.app.auth.login("owner", "correct horse battery staple")["access_token"]
        self.engine.add_memory("episodic", "Preferência", "A cor favorita é azul.")
        sid = self.request("/api/v1/sessions", "POST", {}, self.owner)["body"]["id"]
        with patch.dict(os.environ, {"NEXUS_TOOL_CALLING_MODELS": "ollama:qwen-offline-test"}):
            reply = self.request(f"/api/v1/sessions/{sid}/messages", "POST",
                                 {"content": "Qual é minha cor favorita?"}, self.owner)
        self.assertTrue(reply["status"].startswith("200"), reply["body"])
        self.assertEqual(reply["body"]["message"]["content"], "A memória encontrada diz azul.")
        self.assertEqual(len(provider.calls), 2)
        self.assertIn("UNTRUSTED TOOL RESULT", provider.assert_result)
        self.assertEqual(provider.calls[0][1][0]["function"]["name"], "memory.search")

    def test_opt_in_specialists_run_before_final_response_and_record_metadata(self):
        import os
        from unittest.mock import patch
        provider = SpecialistAwareProvider()
        provider.provider_name = "ollama"
        self.app.provider_manager.injected_provider = provider
        with self.engine.db() as c:
            c.execute("UPDATE provider_settings SET provider='ollama',model=? WHERE id=1", (provider.model,))
        sid = self.request("/api/v1/sessions", "POST", {}, self.owner)["body"]["id"]
        with patch.dict(os.environ, {"NEXUS_MULTIAGENT_ENABLED": "true"}):
            reply = self.request(f"/api/v1/sessions/{sid}/messages", "POST",
                                 {"content": "Analise e planeje uma melhoria"}, self.owner)
        self.assertTrue(reply["status"].startswith("200"), reply["body"])
        self.assertEqual(len(provider.calls), 4)
        final_prompt = json.dumps(provider.calls[-1], ensure_ascii=False)
        self.assertIn("architect result", final_prompt)
        self.assertIn("analyst result", final_prompt)
        self.assertIn("reviewer result", final_prompt)
        self.assertEqual(provider.calls[-1][-1], {"role": "user", "content": "Analise e planeje uma melhoria"})
        with self.engine.db() as c:
            records = [json.loads(row[0]) for row in c.execute(
                "SELECT details FROM api_activity WHERE event LIKE 'agent.llm_call_%'").fetchall()]
        self.assertEqual(len(records), 6)
        self.assertNotIn("architect result", json.dumps(records))

    def test_agent_activity_endpoint_is_authenticated_isolated_and_metadata_only(self):
        owner_user = self.app.auth.user_for_token(self.owner)
        self.app.agents.record(owner_user["id"], "agent.llm_call_completed", {
            "agent_id": "reviewer",
            "provider": "ollama",
            "model": "review-model",
            "status": "completed",
            "duration_ms": 123,
            "input_chars": 456,
            "output_chars": 78,
            "task_id": "task_private_12345678",
            "prompt": "PRIVATE PROMPT MUST NOT BE RETURNED",
            "response": "PRIVATE MODEL RESPONSE MUST NOT BE RETURNED",
            "tool_result": {"secret": "PRIVATE TOOL DATA"},
        })
        # Simulate an activity row owned by another local identity without
        # creating a second login account (the product supports one local owner).
        self.app.agents.record("different-owner-id", "agent.llm_call_completed", {
            "agent_id": "analyst", "provider": "ollama", "model": "other-user-model",
        })
        self.app.tools._audit(owner_user["id"], "tool.completed", "knowledge.claims", {
            "permission": "READ", "risk": "READ", "decision": "allowed",
            "duration_ms": 17, "arguments": "PRIVATE TOOL ARGUMENT",
            "result": "PRIVATE TOOL RESULT",
        })
        self.app.tools._audit("different-owner-id", "tool.completed", "private.tool", {
            "permission": "READ", "risk": "READ", "decision": "allowed",
        })
        job_id = self.app.queue.enqueue(
            "learning.stats", {"private_payload": "PRIVATE JOB PAYLOAD"},
            owner_id=owner_user["id"],
        )
        claimed = self.app.queue.claim(owner_id=owner_user["id"])
        self.assertEqual(claimed["id"], job_id)
        self.app.queue.complete(
            job_id, {"private_result": "PRIVATE JOB RESULT"},
            lease_token=claimed["lease_token"],
        )
        self.app.queue.enqueue(
            "learning.stats", {"private_payload": "OTHER USER JOB"},
            owner_id="different-owner-id",
        )

        unauthenticated = self.request("/api/v1/agents/activity")
        self.assertTrue(unauthenticated["status"].startswith("401"))
        response = self.request("/api/v1/agents/activity", token=self.owner)
        self.assertTrue(response["status"].startswith("200"), response)
        self.assertEqual(len(response["body"]), 5)
        by_event = {event["event"]: event for event in response["body"]}
        event = by_event["agent.llm_call_completed"]
        self.assertEqual(event["details"]["agent_id"], "reviewer")
        self.assertEqual(event["details"]["provider"], "ollama")
        self.assertEqual(event["details"]["duration_ms"], 123)
        tool_event = by_event["tool.completed"]
        self.assertEqual(tool_event["details"]["tool"], "knowledge.claims")
        self.assertEqual(tool_event["details"]["permission"], "READ")
        self.assertEqual(tool_event["details"]["duration_ms"], 17)
        self.assertNotIn("arguments", tool_event["details"])
        self.assertNotIn("result", tool_event["details"])
        job_events = [event for event in response["body"] if event["event"].startswith("job.")]
        self.assertEqual({event["event"] for event in job_events},
                         {"job.queued", "job.claimed", "job.completed"})
        completed_job = next(event for event in job_events if event["event"] == "job.completed")
        self.assertEqual(completed_job["details"]["kind"], "learning.stats")
        self.assertEqual(completed_job["details"]["state"], "completed")
        self.assertEqual(completed_job["details"]["job_id"], job_id)
        serialized = json.dumps(response["body"])
        self.assertNotIn("PRIVATE PROMPT", serialized)
        self.assertNotIn("PRIVATE MODEL RESPONSE", serialized)
        self.assertNotIn("PRIVATE TOOL DATA", serialized)
        self.assertNotIn("PRIVATE TOOL ARGUMENT", serialized)
        self.assertNotIn("PRIVATE TOOL RESULT", serialized)
        self.assertNotIn("PRIVATE JOB PAYLOAD", serialized)
        self.assertNotIn("PRIVATE JOB RESULT", serialized)
        self.assertNotIn("OTHER USER JOB", serialized)
        self.assertNotIn("other-user-model", serialized)
        self.assertNotIn("private.tool", serialized)

    def test_opt_in_specialists_can_use_independent_provider_models(self):
        import os
        from unittest.mock import patch
        from nexus_learning.providers.base import ModelResponse

        class StageProvider:
            provider_name = "ollama"
            def __init__(self, model, summary):
                self.model = model
                self.summary = summary
                self.calls = 0
            def generate(self, messages, *, max_tokens=800, timeout=30):
                self.calls += 1
                role = messages[0]["content"].lower()
                payload = {"summary": self.summary, "items": [], "claims": []}
                if "analyst specialist" in role:
                    payload["claims"] = [{"text": "uncited observation", "evidence_ids": []}]
                if "reviewer specialist" in role:
                    payload["reviews"] = [{"claim_index": 0, "assessment": "unsupported",
                                          "note": "No source was supplied."}]
                return ModelResponse(json.dumps(payload), self.provider_name, self.model)

        main = RecordingProvider()
        main.provider_name = "ollama"
        main.model = "main-model"
        selected = {
            "architect-model": StageProvider("architect-model", "architect"),
            "analyst-model": StageProvider("analyst-model", "analyst"),
            "reviewer-model": StageProvider("reviewer-model", "reviewer"),
        }
        self.app.provider_manager.injected_provider = main
        with self.engine.db() as c:
            c.execute("UPDATE provider_settings SET provider='ollama',model=? WHERE id=1",
                      (main.model,))
        original_build = self.app.provider_manager.build

        def build(name, model=None):
            if name == "ollama" and model == main.model:
                return main
            if name == "ollama" and model in selected:
                return selected[model]
            return original_build(name, model)

        config = json.dumps({
            "architect": "ollama:architect-model",
            "analyst": "ollama:analyst-model",
            "reviewer": "ollama:reviewer-model",
        })
        sid = self.request("/api/v1/sessions", "POST", {}, self.owner)["body"]["id"]
        with patch.dict(os.environ, {"NEXUS_MULTIAGENT_ENABLED": "true",
                                     "NEXUS_AGENT_MODELS": config}):
            with patch.object(self.app.provider_manager, "build", side_effect=build):
                reply = self.request(f"/api/v1/sessions/{sid}/messages", "POST",
                                     {"content": "Analise e planeje uma melhoria"}, self.owner)

        self.assertTrue(reply["status"].startswith("200"), reply["body"])
        self.assertEqual([selected[name].calls for name in selected], [1, 1, 1])
        self.assertEqual(len(main.messages), 4)  # runtime system, skill/context, deliverables and final user turn
        final_context = json.dumps(main.messages, ensure_ascii=False)
        self.assertIn("architect", final_context)
        self.assertIn("analyst", final_context)
        self.assertIn("reviewer", final_context)
        self.assertIn("unsupported", final_context)
        self.assertIn("claims_rejected_by_review", final_context)
        self.assertNotIn("uncited observation", final_context)

    def test_opt_in_specialists_skip_simple_conversation(self):
        import os
        from unittest.mock import patch
        provider = SpecialistAwareProvider()
        provider.provider_name = "ollama"
        self.app.provider_manager.injected_provider = provider
        with self.engine.db() as c:
            c.execute("UPDATE provider_settings SET provider='ollama',model=? WHERE id=1", (provider.model,))
        sid = self.request("/api/v1/sessions", "POST", {}, self.owner)["body"]["id"]
        with patch.dict(os.environ, {"NEXUS_MULTIAGENT_ENABLED": "true"}):
            reply = self.request(f"/api/v1/sessions/{sid}/messages", "POST",
                                 {"content": "Oi"}, self.owner)
        self.assertTrue(reply["status"].startswith("200"), reply["body"])
        self.assertEqual(len(provider.calls), 1)

    def test_remote_specialists_fail_closed_when_budget_is_unavailable(self):
        import os
        from unittest.mock import patch

        class Remote(SpecialistAwareProvider):
            provider_name = "gemini"

        provider = Remote()
        provider.provider_name = "gemini"
        self.app.provider_manager.injected_provider = provider
        with self.engine.db() as c:
            c.execute("UPDATE provider_settings SET provider='gemini',model=? WHERE id=1", (provider.model,))
        sid = self.request("/api/v1/sessions", "POST", {}, self.owner)["body"]["id"]
        with patch.dict(os.environ, {"NEXUS_MULTIAGENT_ENABLED": "true"}):
            reply = self.request(f"/api/v1/sessions/{sid}/messages", "POST",
                                 {"content": "Analise e planeje uma melhoria"}, self.owner)
        self.assertTrue(reply["status"].startswith("429"), reply["body"])
        self.assertEqual(provider.calls, [])
        self.assertEqual(reply["body"]["code"], "multiagent_budget_unavailable")

    def test_remote_specialists_and_final_call_are_all_budgeted(self):
        import os
        from unittest.mock import patch

        class Remote(SpecialistAwareProvider):
            pass

        provider = Remote()
        provider.provider_name = "gemini"
        self.app.provider_manager.injected_provider = provider
        with self.engine.db() as c:
            c.execute("UPDATE provider_settings SET provider='gemini',model=? WHERE id=1", (provider.model,))
        self.app.provider_budget.update(enabled=True, daily_calls=10, daily_tokens=100_000,
            daily_usd=1, task_calls=10, task_tokens=100_000, task_usd=1,
            input_price=1, output_price=1)
        sid = self.request("/api/v1/sessions", "POST", {}, self.owner)["body"]["id"]
        with patch.dict(os.environ, {"NEXUS_MULTIAGENT_ENABLED": "true"}):
            reply = self.request(f"/api/v1/sessions/{sid}/messages", "POST",
                                 {"content": "Analise e planeje uma melhoria"}, self.owner)
        self.assertTrue(reply["status"].startswith("200"), reply["body"])
        with self.engine.db() as c:
            usages = c.execute("SELECT state FROM provider_usage WHERE task_id=?",
                               (reply["body"]["task_id"],)).fetchall()
        self.assertEqual(len(usages), 4)
        self.assertTrue(all(row["state"] == "settled" for row in usages))

    def test_opt_in_specialists_are_run_before_streamed_final_answer(self):
        import os
        from unittest.mock import patch
        provider = SpecialistAwareProvider()
        provider.provider_name = "ollama"
        self.app.provider_manager.injected_provider = provider
        with self.engine.db() as c:
            c.execute("UPDATE provider_settings SET provider='ollama',model=? WHERE id=1", (provider.model,))
        sid = self.request("/api/v1/sessions", "POST", {}, self.owner)["body"]["id"]
        with patch.dict(os.environ, {"NEXUS_MULTIAGENT_ENABLED": "true"}):
            reply = self.request(f"/api/v1/sessions/{sid}/messages/stream", "POST",
                                 {"content": "Analise e planeje o fluxo"}, self.owner)
        self.assertTrue(reply["status"].startswith("200"))
        body = reply["body"].decode("utf-8")
        self.assertIn('event: start', body)
        self.assertIn('event: delta', body)
        self.assertIn('event: done', body)
        self.assertEqual(len(provider.calls), 3)
        self.assertIn("reviewer result", json.dumps(provider.messages, ensure_ascii=False))

    def test_failed_specialist_stage_does_not_call_final_provider(self):
        import os
        from unittest.mock import patch
        from nexus_learning.providers.base import ModelResponse

        class MalformedSpecialist(SpecialistAwareProvider):
            def generate(self, messages, *, max_tokens=800, timeout=30, task_id=None):
                self.calls.append(messages)
                return ModelResponse("not-json", "ollama", self.model)

        provider = MalformedSpecialist()
        provider.provider_name = "ollama"
        self.app.provider_manager.injected_provider = provider
        with self.engine.db() as c:
            c.execute("UPDATE provider_settings SET provider='ollama',model=? WHERE id=1", (provider.model,))
        sid = self.request("/api/v1/sessions", "POST", {}, self.owner)["body"]["id"]
        with patch.dict(os.environ, {"NEXUS_MULTIAGENT_ENABLED": "true"}):
            reply = self.request(f"/api/v1/sessions/{sid}/messages", "POST",
                                 {"content": "Analise e planeje uma melhoria"}, self.owner)
        self.assertTrue(reply["status"].startswith("502"), reply["body"])
        self.assertEqual(len(provider.calls), 1)
        task = self.request("/api/v1/tasks/" + reply["body"]["task_id"], token=self.owner)
        self.assertEqual(task["body"]["state"], "failed")
        self.assertIn("specialist_pipeline_failed", task["body"]["error"])

    def test_chat_research_requires_confirmation_and_synthesizes_attributed_results(self):
        class FakeTavily:
            calls=0
            def search(self, query, *, depth, limit):
                self.calls+=1
                return [{"provider":"tavily","external_id":"https://example.org/weather",
                         "url":"https://example.org/weather","title":"Official weather report",
                         "abstract":"Rain expected tomorrow.","publication_date":"2026-11-01",
                         "score":0.92,"source_class":"web_search_result",
                         "metadata":{"content_is_untrusted":True}}]

        fake=FakeTavily()
        self.app.integrations.env={"NEXUS_TAVILY_ENABLED":"true","TAVILY_API_KEY":"test-only"}
        self.app.integrations.tavily=lambda:fake
        self.provider.response="A fonte consultada indica chuva esperada amanhã [S1]."
        sid=self.request("/api/v1/sessions","POST",{},self.owner)["body"]["id"]
        query="Pesquise fontes confiáveis sobre a previsão do tempo."
        pending=self.request(f"/api/v1/sessions/{sid}/messages/stream","POST",
                             {"content":query},self.owner)
        self.assertTrue(pending["status"].startswith("409"))
        self.assertEqual(pending["body"]["code"],"research_confirmation_required")
        self.assertEqual(fake.calls,0)
        self.assertEqual(self.request(f"/api/v1/sessions/{sid}/messages",token=self.owner)["body"],[])
        oversized=self.request(f"/api/v1/sessions/{sid}/messages","POST",
            {"content":"Pesquise fontes " + "x"*400,"confirm_research":True},self.owner)
        self.assertTrue(oversized["status"].startswith("400"))
        self.assertEqual(fake.calls,0)

        confirmed=self.request(f"/api/v1/sessions/{sid}/messages","POST",
            {"content":query,"confirm_research":True},self.owner)
        self.assertTrue(confirmed["status"].startswith("200"),confirmed["body"])
        self.assertEqual(fake.calls,1)
        self.assertIn("https://example.org/weather", "\n".join(m["content"] for m in self.provider.messages))
        self.assertIn("untrusted", "\n".join(m["content"] for m in self.provider.messages).lower())
        self.assertEqual(confirmed["body"]["sources"][0]["url"],"https://example.org/weather")
        history=self.request(f"/api/v1/sessions/{sid}/research",token=self.owner)
        self.assertEqual(history["body"][0]["sources"],confirmed["body"]["sources"])
        self.assertEqual(history["body"][0]["source_ids"],
                         [source["id"] for source in confirmed["body"]["sources"]])

    def test_streaming_research_confirmation_returns_sources_before_model_completion(self):
        class FakeTavily:
            calls=0
            def search(self, query, *, depth, limit):
                self.calls+=1
                return [{"provider":"tavily","external_id":"https://example.org/a",
                    "url":"https://example.org/a","title":"Source A","abstract":"Evidence A",
                    "publication_date":None,"score":0.8,"source_class":"web_search_result",
                    "metadata":{"content_is_untrusted":True}}]
        fake=FakeTavily()
        self.app.integrations.env={"NEXUS_TAVILY_ENABLED":"true","TAVILY_API_KEY":"test-only"}
        self.app.integrations.tavily=lambda:fake
        self.provider.response="Supported statement [S1]."
        sid=self.request("/api/v1/sessions","POST",{},self.owner)["body"]["id"]
        content="Pesquise fontes sobre renováveis"
        pending=self.request(f"/api/v1/sessions/{sid}/messages/stream","POST",
                             {"content":content},self.owner)
        self.assertTrue(pending["status"].startswith("409"))
        self.assertEqual(fake.calls,0)
        result=self.request(f"/api/v1/sessions/{sid}/messages/stream","POST",
                            {"content":content,"confirm_research":True},self.owner)
        self.assertTrue(result["status"].startswith("200"), (result["status"], result["body"]))
        payload=result["body"].decode("utf-8")
        self.assertIn("event: sources",payload)
        self.assertIn("event: done",payload)
        self.assertIn("https://example.org/a",payload)
        self.assertEqual(fake.calls,1)

    def test_bad_payload_tool_allowlist_and_logout(self):
        bad = self.request("/api/v1/sessions", "POST", {"title": " "}, self.owner)
        self.assertTrue(bad["status"].startswith("400"))
        denied = self.request("/api/v1/tools/unknown/execute", "POST", {"arguments": {}}, self.owner)
        self.assertTrue(denied["status"].startswith("403"))
        tool = self.request("/api/v1/tools/memory.search/execute", "POST",
                            {"arguments": {"query": "absent"}}, self.owner)
        self.assertTrue(tool["status"].startswith("200"))
        self.request("/api/v1/auth/logout", "POST", {}, self.owner)
        self.assertTrue(self.request("/api/v1/sessions", token=self.owner)["status"].startswith("401"))

    def test_explicit_memory_write_and_claim_validation_require_confirmation_and_source(self):
        denied = self.request("/api/v1/memories", "POST", {"kind": "semantic", "title": "x", "body": "y"}, self.owner)
        self.assertTrue(denied["status"].startswith("403"))
        saved = self.request("/api/v1/memories", "POST", {"kind": "episodic", "title": "note",
                                                              "body": "explicitly saved experience", "confirm": True}, self.owner)
        memory = self.engine.search_memories("experience")[0]
        self.assertEqual(memory["id"], saved["body"]["id"])
        proposed = self.request("/api/v1/claims", "POST", {"claim": "A claim", "confirm": True}, self.owner)
        claim_id = proposed["body"]["id"]
        rejected = self.request(f"/api/v1/claims/{claim_id}/review", "POST",
                                {"state": "validated", "rationale": "reviewed", "confidence": .9, "confirm": True}, self.owner)
        self.assertTrue(rejected["status"].startswith("400"))
        self.assertEqual(self.engine.get_claim(claim_id)["state"], "proposed")

    def test_jobs_are_owner_scoped_and_not_executable_cross_user(self):
        created = self.request("/api/v1/jobs", "POST", {"kind": "learning.stats",
                                                              "idempotency_key": "owner-job"}, self.owner)
        job_id = created["body"]["id"]
        other_job = self.app.queue.enqueue("learning.stats", owner_id="another-user")
        self.assertEqual([x["id"] for x in self.request("/api/v1/jobs", token=self.owner)["body"]], [job_id])
        self.assertTrue(self.request(f"/api/v1/jobs/{other_job}", token=self.owner)["status"].startswith("404"))
        self.assertTrue(self.request("/api/v1/jobs/run-once", "POST", {}, self.owner)["body"]["processed"])
        self.assertEqual(self.app.queue.get(other_job)["state"], "queued")

    def test_integration_status_and_model_budget_are_authenticated_and_fail_closed(self):
        status=self.request('/api/v1/integrations',token=self.owner)
        self.assertEqual(status['body']['crossref']['configured'],True)
        self.assertNotIn('api_key',json.dumps(status['body']).casefold())
        self.assertTrue(self.request('/api/v1/integrations/usage',token=self.owner)['status'].startswith('200'))
        self.assertTrue(self.request('/api/v1/usage/budget','POST',{'confirm':True,'enabled':True},self.owner)['status'].startswith('400'))
        body={'confirm':True,'enabled':True,'daily_calls':5,'daily_tokens':50000,'daily_usd':2.0,
              'task_calls':2,'task_tokens':12000,'task_usd':0.5,
              'input_usd_per_million':0.1,'output_usd_per_million':0.4}
        saved=self.request('/api/v1/usage/budget','POST',body,self.owner)
        self.assertEqual(saved['body']['enabled'],True)
        self.assertTrue(self.request('/api/v1/usage',token=self.owner)['status'].startswith('200'))
        self.assertTrue(self.request('/api/v1/usage/budget','POST',body)['status'].startswith('401'))

    def test_integration_health_check_is_explicit_and_never_returns_raw_secrets(self):
        self.app.integrations.env={"NEXUS_PROVIDER":"mock","NEXUS_ENABLE_REMOTE_PROVIDER":"false",
                                   "NEXUS_TAVILY_ENABLED":"false","NEXUS_GITHUB_ENABLED":"true"}
        denied=self.request('/api/v1/integrations/check','POST',{'providers':['tavily']},self.owner)
        self.assertTrue(denied['status'].startswith('403'))
        result=self.request('/api/v1/integrations/check','POST',{'confirm':True,'providers':['gemini']},self.owner)
        self.assertTrue(result['status'].startswith('200'))
        self.assertEqual(result['body']['results'][0]['status'],'not_configured_or_disabled')
        self.assertNotIn('api_key',json.dumps(result['body']).casefold())

    def test_connection_checks_do_not_generate_tokens_or_spend_tavily_search_credits(self):
        self.app.integrations.env={"NEXUS_PROVIDER":"ollama","NEXUS_ENABLE_REMOTE_PROVIDER":"true",
            "NEXUS_REMOTE_PROVIDERS":"gemini",
            "GEMINI_API_KEY":"fake-key","GEMINI_MODEL":"gemini-test",
            "NEXUS_TAVILY_ENABLED":"true","TAVILY_API_KEY":"fake-tavily-key"}
        self.app.provider_manager.check=lambda name:{"provider":name,"available":True,"model_count":2}
        class UsageOnlyTavily:
            def usage(self): return {"key":{"usage":7,"limit":100}}
            def search(self,*args,**kwargs): raise AssertionError("connection test must not consume search credits")
        self.app.integrations.tavily=lambda:UsageOnlyTavily()
        self.app.runtime_provider.generate=lambda *args,**kwargs: (_ for _ in ()).throw(
            AssertionError("connection test must not generate a model response"))
        response=self.request('/api/v1/integrations/check','POST',
            {'confirm':True,'providers':['gemini','tavily']},self.owner)
        self.assertTrue(response['status'].startswith('200'))
        statuses={row['provider']:row for row in response['body']['results']}
        self.assertEqual(statuses['gemini']['status'],'connected')
        self.assertEqual(statuses['gemini']['model_count'],2)
        self.assertEqual(statuses['tavily']['status'],'connected')
        self.assertEqual(statuses['tavily']['usage']['key']['usage'],7)

    def test_tavily_routes_require_opt_in_confirmation_and_register_untrusted_sources(self):
        manager=self.app.integrations
        manager.env={'NEXUS_TAVILY_ENABLED':'true','TAVILY_API_KEY':'fake-key','NEXUS_TAVILY_DAILY_CALL_LIMIT':'5'}
        class FakeTavily:
            def search(self,query,*,depth,limit):
                return [{'url':'https://example.org/page','title':'External page','abstract':'untrusted snippet','provider':'tavily','score':.7}]
            def extract(self,urls,*,depth): return [{'url':urls[0],'content':'untrusted page text','content_is_untrusted':True}]
        manager.tavily=lambda:FakeTavily()
        denied=self.request('/api/v1/integrations/tavily/search','POST',{'query':'topic'},self.owner)
        self.assertTrue(denied['status'].startswith('403'))
        result=self.request('/api/v1/integrations/tavily/search','POST',{'confirm':True,'query':'topic'},self.owner)
        self.assertTrue(result['status'].startswith('200'))
        self.assertEqual(result['body']['results'][0]['provider'],'tavily')
        extracted=self.request('/api/v1/integrations/tavily/extract','POST',{'confirm':True,'urls':['https://example.org/page']},self.owner)
        self.assertTrue(extracted['status'].startswith('200'),extracted['body'])
        documents=self.request('/api/v1/integrations/documents',token=self.owner)['body']
        self.assertEqual(documents[0]['trust_label'],'external_untrusted')

    def test_github_tracking_api_is_read_only_and_owner_scoped(self):
        manager=self.app.integrations
        created=self.request('/api/v1/integrations/github/repos','POST',{'confirm':True,'owner':'octo','repo':'project'},self.owner)
        self.assertTrue(created['status'].startswith('201'))
        class FakeGitHub:
            def repository(self,*a): return {'full_name':'octo/project','pushed_at':'2026-01-01'}
            def commits(self,*a,**k): return [{'sha':'abc','message':'update','date':'2026-01-01','url':'https://github.com/octo/project/commit/abc'}]
            def issues(self,*a,**k): return []
        manager.github=lambda:FakeGitHub()
        synced=self.request('/api/v1/integrations/github/repos/'+created['body']['id']+'/sync','POST',{'confirm':True},self.owner)
        self.assertTrue(synced['status'].startswith('200'))
        self.assertEqual(len(synced['body']['changes']['new_commits']),1)

    def test_auth_store_enforces_single_owner(self):
        with self.assertRaises(ValueError):
            self.app.auth.create_user("second", "another secure password")


if __name__ == "__main__":
    unittest.main()
