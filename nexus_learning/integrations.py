"""Read-only external integrations with bounded requests and secret-safe errors."""
import json
import ipaddress
import math
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .providers.errors import (ProviderAuthenticationError, ProviderConfigurationError,
    ProviderRateLimitError, ProviderResponseError, ProviderTimeoutError,
    ProviderUnavailableError)

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

_DEFAULT_OPEN = build_opener(_NoRedirect()).open

def _public_http_url(value):
    if not isinstance(value,str) or len(value)>2048: return False
    try:
        parsed=urlsplit(value)
        if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password: return False
        host=parsed.hostname.casefold().rstrip('.')
        if host in {'localhost','localhost.localdomain'} or host.endswith(('.local','.internal','.lan')): return False
        try:
            address=ipaddress.ip_address(host)
            if not address.is_global: return False
        except ValueError: pass
        return True
    except (ValueError,TypeError): return False

is_public_http_url = _public_http_url

class IntegrationHTTP:
    def __init__(self, opener=None, timeout=20, max_response=2_000_000):
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0 < timeout <= 60:
            raise ValueError('timeout out of range')
        self.opener = opener or _DEFAULT_OPEN
        self.timeout, self.max_response = float(timeout), max_response

    def request_json(self, url, *, method='GET', headers=None, payload=None):
        data = None if payload is None else json.dumps(payload).encode('utf-8')
        request = Request(url, data=data, headers=headers or {}, method=method)
        try:
            with self.opener(request, timeout=self.timeout) as response:
                raw = response.read(self.max_response + 1)
            if len(raw) > self.max_response:
                raise ProviderResponseError()
            return json.loads(raw.decode('utf-8'))
        except HTTPError as exc:
            if exc.code in (401, 403): raise ProviderAuthenticationError() from None
            if exc.code == 429:
                retry = None
                try:
                    retry = max(0.0, min(3600.0, float(exc.headers.get('Retry-After'))))
                except (TypeError, ValueError): pass
                raise ProviderRateLimitError(retry_after=retry) from None
            if exc.code in (408, 504): raise ProviderTimeoutError() from None
            if exc.code >= 500: raise ProviderUnavailableError() from None
            raise ProviderResponseError() from None
        except TimeoutError: raise ProviderTimeoutError() from None
        except URLError as exc:
            if isinstance(getattr(exc, 'reason', None), TimeoutError): raise ProviderTimeoutError() from None
            raise ProviderUnavailableError() from None
        except (json.JSONDecodeError, UnicodeDecodeError): raise ProviderResponseError() from None

class TavilyClient:
    BASE = 'https://api.tavily.com'
    def __init__(self, api_key, *, http=None):
        if not isinstance(api_key, str) or not api_key.strip(): raise ProviderConfigurationError()
        self._key, self.http = api_key.strip(), http or IntegrationHTTP()
    def _post(self, endpoint, body):
        return self.http.request_json(self.BASE + endpoint, method='POST',
            headers={'Authorization':'Bearer '+self._key,'Content-Type':'application/json','Accept':'application/json'}, payload=body)
    def usage(self):
        """Read account/key usage without issuing a credit-consuming search."""
        payload=self.http.request_json(self.BASE + '/usage',
            headers={'Authorization':'Bearer '+self._key,'Accept':'application/json'})
        if not isinstance(payload,dict): raise ProviderResponseError()
        result={}
        for group,fields in {'key':('usage','limit','search_usage','extract_usage'),
                             'account':('current_plan','plan_usage','plan_limit','paygo_usage','paygo_limit')}.items():
            values=payload.get(group,{})
            if not isinstance(values,dict): raise ProviderResponseError()
            clean={}
            for field in fields:
                value=values.get(field)
                if value is not None and not isinstance(value,(int,str)):
                    raise ProviderResponseError()
                if isinstance(value,bool): raise ProviderResponseError()
                if isinstance(value,str): value=value[:80]
                clean[field]=value
            result[group]=clean
        return result
    def search(self, query, *, depth='basic', limit=5, include_raw_content=False):
        if not isinstance(query,str) or not query.strip() or len(query)>400: raise ValueError('invalid query')
        if depth not in {'basic','advanced'} or isinstance(limit,bool) or not isinstance(limit,int) or not 1<=limit<=10: raise ValueError('invalid search options')
        response=self._post('/search', {'query':query.strip(),'search_depth':depth,'max_results':limit,
            'include_answer':False,'include_raw_content':bool(include_raw_content),'include_published_date':True})
        rows=response.get('results')
        if not isinstance(rows,list): raise ProviderResponseError()
        result=[]
        for row in rows[:limit]:
            if not isinstance(row,dict) or not _public_http_url(row.get('url')): continue
            result.append({'provider':'tavily','external_id':row['url'],'url':row['url'],
                'title':str(row.get('title') or row['url'])[:500], 'abstract':str(row.get('raw_content') or row.get('content') or '')[:1200],
                'publication_date':row.get('published_date') if isinstance(row.get('published_date'),str) else None,
                'score':_safe_score(row.get('score')),'source_class':'web_search_result',
                'metadata':{'content_is_untrusted':True,'search_depth':depth}})
        return result
    def extract(self, urls, *, depth='basic'):
        if not isinstance(urls,list) or not 1<=len(urls)<=5 or depth not in {'basic','advanced'}: raise ValueError('invalid extraction request')
        for url in urls:
            if not _public_http_url(url): raise ValueError('URL must be a public HTTP(S) address')
        response=self._post('/extract', {'urls':urls,'extract_depth':depth,'format':'markdown'})
        rows=response.get('results')
        if not isinstance(rows,list): raise ProviderResponseError()
        return [{'url':r['url'],'content':str(r.get('raw_content') or '')[:12000],
                 'content_is_untrusted':True} for r in rows if isinstance(r,dict) and r.get('url') in urls]

class GitHubClient:
    BASE='https://api.github.com'
    def __init__(self, token=None, *, http=None):
        if token is not None and (not isinstance(token,str) or len(token)>4096): raise ProviderConfigurationError()
        self._token=token.strip() if token else None
        self.http=http or IntegrationHTTP()
    def _get(self,path,query=None):
        if not path.startswith('/') or '..' in path: raise ValueError('invalid GitHub path')
        headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2026-03-10','User-Agent':'NEXUS-local-research'}
        if self._token: headers['Authorization']='Bearer '+self._token
        url=self.BASE+path+(('?'+urlencode(query)) if query else '')
        return self.http.request_json(url,headers=headers)
    @staticmethod
    def _repo(owner,repo):
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',owner or '') or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',repo or ''): raise ValueError('invalid repository')
        return quote(owner,safe=''),quote(repo,safe='')
    def health(self):
        data=self._get('/rate_limit')
        if not isinstance(data,dict) or not isinstance(data.get('resources'),dict): raise ProviderResponseError()
        core=data['resources'].get('core',{})
        return {'authenticated':bool(self._token),'remaining':core.get('remaining'),'limit':core.get('limit')}
    def repository(self,owner,repo):
        o,r=self._repo(owner,repo); x=self._get(f'/repos/{o}/{r}')
        return {k:x.get(k) for k in ('full_name','html_url','description','default_branch','visibility','updated_at','pushed_at','open_issues_count','stargazers_count')}
    def commits(self,owner,repo,*,since=None,limit=10):
        o,r=self._repo(owner,repo)
        if isinstance(limit,bool) or not isinstance(limit,int) or not 1<=limit<=30: raise ValueError('invalid limit')
        query={'per_page':limit}
        if since is not None:
            if not isinstance(since,str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ',since): raise ValueError('invalid since')
            query['since']=since
        rows=self._get(f'/repos/{o}/{r}/commits',query)
        if not isinstance(rows,list): raise ProviderResponseError()
        return [{'sha':x.get('sha'),'message':str(x.get('commit',{}).get('message',''))[:500],
                 'date':x.get('commit',{}).get('committer',{}).get('date'),'url':x.get('html_url')} for x in rows if isinstance(x,dict)]
    def issues(self,owner,repo,*,state='open',limit=10):
        o,r=self._repo(owner,repo)
        if state not in {'open','closed','all'} or isinstance(limit,bool) or not isinstance(limit,int) or not 1<=limit<=30: raise ValueError('invalid issue options')
        rows=self._get(f'/repos/{o}/{r}/issues',{'state':state,'per_page':limit,'sort':'updated','direction':'desc'})
        if not isinstance(rows,list): raise ProviderResponseError()
        return [{'number':x.get('number'),'title':str(x.get('title') or '')[:500],
                 'state':x.get('state'),'updated_at':x.get('updated_at'),'html_url':x.get('html_url'),
                 'is_pull_request':'pull_request' in x} for x in rows if isinstance(x,dict)]

def _safe_score(value):
    try:
        n=float(value)
        return n if math.isfinite(n) and 0<=n<=1 else None
    except (TypeError,ValueError): return None

class IntegrationManager:
    """Reports safe integration state and provides bounded read-only operations."""
    def __init__(self,environ=None,engine=None):
        import os
        from .engine import now
        self.env=os.environ if environ is None else environ
        self.engine=engine
        if engine is not None:
            with engine.db() as c:
                c.executescript('''CREATE TABLE IF NOT EXISTS integration_usage(
                  id TEXT PRIMARY KEY,provider TEXT NOT NULL,request_hash TEXT NOT NULL,
                  status TEXT NOT NULL,created_at TEXT NOT NULL);
                  CREATE TABLE IF NOT EXISTS tracked_repositories(
                  id TEXT PRIMARY KEY,owner_id TEXT NOT NULL,repo_owner TEXT NOT NULL,repo_name TEXT NOT NULL,
                  last_synced TEXT,snapshot_json TEXT NOT NULL DEFAULT '{}',created_at TEXT NOT NULL,
                  UNIQUE(owner_id,repo_owner,repo_name));
                  CREATE TABLE IF NOT EXISTS github_sync_events(
                  id TEXT PRIMARY KEY,tracked_id TEXT NOT NULL,details_json TEXT NOT NULL,created_at TEXT NOT NULL);
                  CREATE TABLE IF NOT EXISTS integration_documents(
                  id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES sources(id),content TEXT NOT NULL,
                  content_hash TEXT NOT NULL,trust_label TEXT NOT NULL,fetched_at TEXT NOT NULL,
                  UNIQUE(source_id,content_hash));''')
    def status(self):
        e=self.env
        allowed_raw=e.get('NEXUS_REMOTE_PROVIDERS')
        allowed={item.strip().lower() for item in allowed_raw.split(',') if item.strip()} if allowed_raw is not None else None
        gemini_enabled=(e.get('NEXUS_ENABLE_REMOTE_PROVIDER','false').lower()=='true'
                        and (allowed is None or 'gemini' in allowed))
        return {
          'gemini':{'enabled':gemini_enabled,'configured':bool(e.get('GEMINI_API_KEY') and e.get('GEMINI_MODEL'))},
          'tavily':{'enabled':e.get('NEXUS_TAVILY_ENABLED','false').lower()=='true','configured':bool(e.get('TAVILY_API_KEY')),
                    'autonomous_approved':e.get('NEXUS_TAVILY_AUTONOMOUS_APPROVED','false').lower()=='true'},
          'crossref':{'enabled':e.get('NEXUS_CROSSREF_ENABLED','true').lower()=='true','configured':True},
          'github':{'enabled':e.get('NEXUS_GITHUB_ENABLED','true').lower()=='true','configured':True,'authenticated':bool(e.get('GITHUB_TOKEN'))},
        }
    def usage(self):
        if self.engine is None:return []
        from datetime import datetime,timezone
        day=datetime.now(timezone.utc).date().isoformat()+'%'
        with self.engine.db() as c:
            return [dict(r) for r in c.execute('SELECT provider,COUNT(*) calls,SUM(CASE WHEN status=\'completed\' THEN 1 ELSE 0 END) completed,SUM(CASE WHEN status=\'failed\' THEN 1 ELSE 0 END) failed FROM integration_usage WHERE created_at LIKE ? GROUP BY provider ORDER BY provider',(day,)).fetchall()]
    def tavily(self): return TavilyClient(self.env.get('TAVILY_API_KEY'))
    def github(self): return GitHubClient(self.env.get('GITHUB_TOKEN'))
    def reserve(self,provider,query,*,daily_limit):
        if self.engine is None: raise RuntimeError('usage ledger is unavailable')
        from .engine import now,uid
        from datetime import datetime,timezone
        import hashlib
        day=datetime.now(timezone.utc).date().isoformat()+'%'
        with self.engine.db() as c:
            c.execute('BEGIN IMMEDIATE')
            used=c.execute('SELECT COUNT(*) FROM integration_usage WHERE provider=? AND created_at LIKE ?',(provider,day)).fetchone()[0]
            if used>=daily_limit: raise RuntimeError('integration daily request limit reached')
            rid=uid('intuse'); c.execute("INSERT INTO integration_usage VALUES(?,?,?,'reserved',?)",(rid,provider,hashlib.sha256(query.encode()).hexdigest(),now()))
        return rid
    def finish(self,reservation,success):
        if self.engine is None:return
        with self.engine.db() as c: c.execute('UPDATE integration_usage SET status=? WHERE id=?',('completed' if success else 'failed',reservation))
    def store_extracted(self,documents):
        from .engine import now,uid
        saved=[]
        for item in documents:
            url=item.get('url',''); content=item.get('content','')
            if not _public_http_url(url) or not isinstance(content,str): continue
            content=content[:12000]
            import hashlib
            digest=hashlib.sha256(content.encode()).hexdigest()
            with self.engine.db() as c:
                row=c.execute('SELECT id,metadata FROM sources WHERE uri=?',(url,)).fetchone()
                known = False
                if row:
                    try:
                        meta=json.loads(row['metadata']); known=meta.get('provider')=='tavily' or 'tavily' in meta.get('discovered_by',[])
                    except (TypeError,ValueError): pass
                    if not known:
                        known=c.execute("SELECT 1 FROM research_records WHERE source_id=? AND provider='tavily'",(row['id'],)).fetchone() is not None
            if not row or not known: raise ValueError('extract only accepts URLs previously discovered through Tavily')
            source_id=row['id']
            doc_id=uid('doc')
            with self.engine.db() as c:
                c.execute('INSERT OR IGNORE INTO integration_documents VALUES(?,?,?,?,?,?)',(doc_id,source_id,content,digest,'external_untrusted',now()))
                row=c.execute('SELECT id FROM integration_documents WHERE source_id=? AND content_hash=?',(source_id,digest)).fetchone()
                saved.append({'id':row['id'],'source_id':source_id,'url':url,'content_is_untrusted':True})
        return saved
    def store_search_sources(self,results):
        saved=[]
        for item in results:
            url=item['url']; title=item['title']
            with self.engine.db() as c: row=c.execute('SELECT id FROM sources WHERE uri=?',(url,)).fetchone()
            if row: source_id=row['id']
            else:
                source_id=self.engine.add_source(url,title)
            with self.engine.db() as c:
                stored=c.execute('SELECT metadata FROM sources WHERE id=?',(source_id,)).fetchone()
                try: meta=json.loads(stored['metadata'])
                except (TypeError,ValueError): meta={}
                discovered=set(meta.get('discovered_by',[]));discovered.add('tavily')
                meta.update({'discovered_by':sorted(discovered),'untrusted':True})
                c.execute('UPDATE sources SET metadata=? WHERE id=?',(json.dumps(meta,sort_keys=True),source_id))
            saved.append(source_id)
        return saved
    def list_repositories(self,owner_id):
        with self.engine.db() as c: return [dict(r) for r in c.execute('SELECT * FROM tracked_repositories WHERE owner_id=? ORDER BY created_at DESC',(owner_id,)).fetchall()]
    def track_repository(self,owner_id,repo_owner,repo_name):
        from .engine import now,uid
        self.github()._repo(repo_owner,repo_name)
        with self.engine.db() as c:
            c.execute('INSERT OR IGNORE INTO tracked_repositories(id,owner_id,repo_owner,repo_name,snapshot_json,created_at) VALUES(?,?,?,?,?,?)',(uid('tracked'),owner_id,repo_owner,repo_name,'{}',now()))
            row=c.execute('SELECT * FROM tracked_repositories WHERE owner_id=? AND repo_owner=? AND repo_name=?',(owner_id,repo_owner,repo_name)).fetchone()
        return dict(row)
    def sync_repository(self,tracked_id,owner_id):
        from .engine import now,uid
        with self.engine.db() as c: row=c.execute('SELECT * FROM tracked_repositories WHERE id=? AND owner_id=?',(tracked_id,owner_id)).fetchone()
        if not row: raise KeyError(tracked_id)
        client=self.github(); repo_owner,repo_name=row['repo_owner'],row['repo_name']
        reservation=self.reserve('github',repo_owner+'/'+repo_name,daily_limit=15)
        try:
            repository=client.repository(repo_owner,repo_name)
            commits=client.commits(repo_owner,repo_name,limit=5)
            issues=client.issues(repo_owner,repo_name,state='open',limit=10)
            previous=json.loads(row['snapshot_json'])
            old={c.get('sha') for c in previous.get('commits',[])}
            current={c.get('sha') for c in commits}
            changes={'new_commits':[c for c in commits if c.get('sha') not in old],
                     'open_issue_count':len(issues),'previous_open_issue_count':previous.get('open_issue_count'),
                     'checked_at':now(),'repository':repository,'content_is_untrusted':True}
            snapshot={'repository':repository,'commits':commits,'open_issue_count':len(issues),'issues':issues,
                      'content_is_untrusted':True}
            with self.engine.db() as c:
                c.execute('UPDATE tracked_repositories SET last_synced=?,snapshot_json=? WHERE id=?',(changes['checked_at'],json.dumps(snapshot,ensure_ascii=False),tracked_id))
                c.execute('INSERT INTO github_sync_events VALUES(?,?,?,?)',(uid('ghsync'),tracked_id,json.dumps(changes,ensure_ascii=False),changes['checked_at']))
            self.finish(reservation,True)
            return {'changes':changes,'snapshot':snapshot}
        except Exception:
            self.finish(reservation,False)
            raise


def _default_manager():
    import os
    return IntegrationManager(os.environ)
