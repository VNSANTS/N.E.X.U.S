import io, json, unittest
from nexus_learning.integrations import TavilyClient, GitHubClient, IntegrationHTTP, IntegrationManager
from nexus_learning.engine import LearningEngine
from nexus_learning.providers.errors import ProviderAuthenticationError, ProviderResponseError
from urllib.error import HTTPError

class Response:
    def __init__(self,obj): self.raw=json.dumps(obj).encode()
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,n=-1): return self.raw[:n]

class IntegrationTests(unittest.TestCase):
    def test_tavily_usage_checks_auth_without_consuming_search_credits(self):
        seen=[]
        def opener(req,timeout):
            seen.append(req)
            return Response({'key':{'usage':12,'limit':100,'search_usage':5},
                             'account':{'current_plan':'Bootstrap','plan_usage':20}})
        usage=TavilyClient('secret-test-key',http=IntegrationHTTP(opener=opener)).usage()
        self.assertEqual(usage['key'],{'usage':12,'limit':100,'search_usage':5,'extract_usage':None})
        self.assertEqual(seen[0].get_method(),'GET')
        self.assertEqual(seen[0].full_url,'https://api.tavily.com/usage')
        self.assertEqual(seen[0].get_header('Authorization'),'Bearer secret-test-key')

    def test_tavily_search_and_extract_are_bounded_and_secret_only_in_auth_header(self):
        seen=[]
        replies=[{'results':[{'url':'https://example.org/a','title':'A','content':'snippet','published_date':'2025-03-01','score':.9}]}, {'results':[{'url':'https://example.org/a','raw_content':'page text'}]}]
        def opener(req,timeout):
            seen.append((req.full_url,dict(req.header_items()),json.loads(req.data),timeout))
            return Response(replies.pop(0))
        client=TavilyClient('secret-test-key',http=IntegrationHTTP(opener=opener))
        rows=client.search('research',limit=2)
        self.assertEqual(rows[0]['provider'],'tavily'); self.assertTrue(rows[0]['metadata']['content_is_untrusted'])
        page=client.extract(['https://example.org/a'])
        self.assertEqual(page[0]['content'],'page text')
        self.assertNotIn('secret-test-key',json.dumps(seen[0][2]))
        self.assertEqual(dict((k.lower(),v) for k,v in seen[0][1].items())['authorization'],'Bearer secret-test-key')
        with self.assertRaises(ValueError): client.extract(['file:///private'])
        with self.assertRaises(ValueError): client.extract(['http://127.0.0.1/admin'])
        with self.assertRaises(ValueError): client.extract(['http://localhost/admin'])
    def test_github_public_repository_commits_and_issues_are_read_only(self):
        seen=[]
        replies=[{'full_name':'octo/repo','html_url':'https://github.com/octo/repo','pushed_at':'2026-01-01T00:00:00Z'},
                 [{'sha':'abc','commit':{'message':'change','committer':{'date':'2026-01-01T00:00:00Z'}},'html_url':'https://github.com/octo/repo/commit/abc'}],
                 [{'number':1,'title':'bug','state':'open','updated_at':'2026-01-02T00:00:00Z','html_url':'https://github.com/octo/repo/issues/1'}]]
        def opener(req,timeout): seen.append(req); return Response(replies.pop(0))
        gh=GitHubClient(http=IntegrationHTTP(opener=opener))
        self.assertEqual(gh.repository('octo','repo')['full_name'],'octo/repo')
        self.assertEqual(gh.commits('octo','repo')[0]['sha'],'abc')
        self.assertFalse(gh.issues('octo','repo')[0]['is_pull_request'])
        self.assertTrue(all(r.get_method()=='GET' for r in seen))
        with self.assertRaises(ValueError): gh.repository('../bad','repo')
    def test_http_auth_and_invalid_response_fail_with_safe_provider_errors(self):
        def denied(req,timeout): raise HTTPError(req.full_url,401,'',{},io.BytesIO(b'secret response'))
        with self.assertRaises(ProviderAuthenticationError) as caught:
            TavilyClient('secret',http=IntegrationHTTP(opener=denied)).search('x')
        self.assertNotIn('secret',str(caught.exception))
        def malformed(req,timeout): return Response({'results':'bad'})
        with self.assertRaises(ProviderResponseError): GitHubClient(http=IntegrationHTTP(opener=malformed)).commits('o','r')

    def test_github_repository_tracking_is_persistent_and_owner_scoped(self):
        engine=LearningEngine(':memory:')
        try:
            manager=IntegrationManager({},engine)
            first=manager.track_repository('owner','octo','nexus')
            manager.track_repository('another','octo','nexus')
            class FakeGitHub:
                def repository(self,*args): return {'full_name':'octo/nexus','pushed_at':'2026-01-01'}
                def commits(self,*args,**kwargs): return [{'sha':'new','message':'Update','date':'2026-01-01','url':'https://github.com/octo/nexus/commit/new'}]
                def issues(self,*args,**kwargs): return []
            manager.github=lambda:FakeGitHub()
            result=manager.sync_repository(first['id'],'owner')
            self.assertEqual(len(result['changes']['new_commits']),1)
            self.assertEqual(len(manager.list_repositories('owner')),1)
            self.assertEqual(len(manager.list_repositories('another')),1)
            with self.assertRaises(KeyError): manager.sync_repository(first['id'],'another')
        finally: engine.close()

    def test_integration_status_never_returns_credentials(self):
        status=IntegrationManager({'NEXUS_PROVIDER':'gemini','NEXUS_ENABLE_REMOTE_PROVIDER':'true',
            'GEMINI_API_KEY':'secret','GEMINI_MODEL':'gemini-test','TAVILY_API_KEY':'secret2'}).status()
        text=json.dumps(status)
        self.assertTrue(status['gemini']['configured']); self.assertNotIn('secret',text)
        self.assertFalse(status['tavily']['enabled'])

    def test_gemini_can_be_enabled_alongside_ollama_default(self):
        status=IntegrationManager({'NEXUS_PROVIDER':'ollama','NEXUS_ENABLE_REMOTE_PROVIDER':'true',
            'NEXUS_REMOTE_PROVIDERS':'gemini','GEMINI_API_KEY':'secret','GEMINI_MODEL':'gemini-test'}).status()
        self.assertTrue(status['gemini']['enabled'])
        self.assertTrue(status['gemini']['configured'])

if __name__=='__main__': unittest.main()
