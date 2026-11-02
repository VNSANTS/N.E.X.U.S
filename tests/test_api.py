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


class APITests(unittest.TestCase):
    def setUp(self):
        self.engine = LearningEngine(":memory:")
        self.provider = RecordingProvider()
        self.app = NexusAPI(self.engine, self.provider)
        self.app.auth.create_user("owner", "correct horse battery staple")
        self.owner = self.app.auth.login("owner", "correct horse battery staple")["access_token"]

    def tearDown(self):
        self.engine.close()

    def request(self, path, method="GET", body=None, token=None, host="127.0.0.1"):
        raw = b"" if body is None else json.dumps(body).encode()
        environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": "",
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

    def test_context_preview_is_authenticated_bounded_and_zero_cost(self):
        self.engine.add_memory("semantic", "Project context", "The project uses local memory")
        denied = self.request("/api/v1/context/preview", "POST", {"query": "project"})
        self.assertTrue(denied["status"].startswith("401"))
        result = self.request("/api/v1/context/preview", "POST", {"query": "project"}, self.owner)
        self.assertTrue(result["status"].startswith("200"), result["body"])
        self.assertTrue(result["body"]["items"])
        self.assertFalse(result["body"]["used_semantic"])
        malformed = self.request("/api/v1/context/preview", "POST",
                                 {"query": "project", "confirm": True}, self.owner)
        self.assertTrue(malformed["status"].startswith("400"))

    def test_claim_review_rejects_malformed_fields_and_returns_evidence_quality(self):
        source = self.engine.add_source("https://example.org/evidence", "Evidence")
        claim = self.engine.propose_claim("A testable claim", [source], {source: "A quoted source excerpt"})
        malformed = self.request(f"/api/v1/claims/{claim}/review", "POST",
            {"state": "validated", "rationale": "Reviewed", "confidence": True, "confirm": True}, self.owner)
        self.assertTrue(malformed["status"].startswith("400"))
        reviewed = self.request(f"/api/v1/claims/{claim}/review", "POST",
            {"state": "validated", "rationale": "Reviewed", "confidence": .85, "confirm": True}, self.owner)
        self.assertTrue(reviewed["status"].startswith("200"), reviewed["body"])
        detail = self.request(f"/api/v1/claims/{claim}", token=self.owner)
        self.assertTrue(detail["body"]["evidence_quality"]["complete"])
        self.assertIn("do not establish", detail["body"]["evidence_quality"]["limitation"])

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
