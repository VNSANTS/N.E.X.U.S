"""Discovery adapters for scientific metadata and web search."""
import os
from .crossref import CrossrefClient
from .integrations import TavilyClient

class TavilyDiscovery:
    name='tavily'
    request_budget=2
    def __init__(self,api_key=None,client=None,usage_manager=None):
        self.client=client or TavilyClient(api_key if api_key is not None else os.environ.get('TAVILY_API_KEY',''))
        self.usage_manager=usage_manager
    def search(self,query,limit=5):
        self.last_failures=[]
        daily_limit=int(self.usage_manager.env.get('NEXUS_TAVILY_DAILY_CALL_LIMIT','5')) if self.usage_manager else 5
        if not 1<=daily_limit<=50: raise ValueError('Tavily daily request limit must be between 1 and 50')
        reservation=self.usage_manager.reserve('tavily',query,daily_limit=daily_limit) if self.usage_manager else None
        try:
            result=self.client.search(query,depth='basic',limit=limit,include_raw_content=False)
            if result and self.usage_manager:
                # Persist discovered URLs before extraction so only vetted public search results are fetched.
                self.usage_manager.store_search_sources(result)
            urls=[x['url'] for x in result[:2]]
            docs=[]
            if urls:
                extract_reservation=None
                try:
                    extract_reservation=self.usage_manager.reserve('tavily','extract:'+ '|'.join(urls),daily_limit=daily_limit) if self.usage_manager else None
                    docs=self.client.extract(urls,depth='basic')
                    if self.usage_manager: self.usage_manager.store_extracted(docs)
                    if extract_reservation:self.usage_manager.finish(extract_reservation,True)
                except Exception:
                    if extract_reservation:self.usage_manager.finish(extract_reservation,False)
                    # Search snippets remain useful and attributed if extraction fails.
                    self.last_failures.append({'operation':'extract','error_type':'external_extraction_failed'})
            by_url={d['url']:d['content'] for d in docs}
            for item in result:
                if by_url.get(item['url']): item['abstract']=by_url[item['url']][:1200]
            if reservation:self.usage_manager.finish(reservation,True)
            return result
        except Exception:
            if reservation:self.usage_manager.finish(reservation,False)
            raise

class CrossrefDiscovery:
    name='crossref'
    def __init__(self,client=None,usage_manager=None):
        self.client=client or CrossrefClient(mailto=os.environ.get('CROSSREF_MAILTO'))
        self.usage_manager=usage_manager
    def search(self,query,limit=5):
        reservation=self.usage_manager.reserve('crossref',query,daily_limit=50) if self.usage_manager else None
        try:
            result=self.client.search(query,limit)
            if reservation:self.usage_manager.finish(reservation,True)
            return result
        except Exception:
            if reservation:self.usage_manager.finish(reservation,False)
            raise

class CompositeDiscovery:
    """Combines approved adapters, preserving successful results if one fails."""
    name='composite'
    def __init__(self,adapters): self.adapters=tuple(adapters)
    @property
    def names(self): return [a.name for a in self.adapters]
    @property
    def request_budget(self): return sum(getattr(a,'request_budget',1) for a in self.adapters)
    def search(self,query,limit=5):
        result=[]; failures=[]
        for adapter in self.adapters:
            adapter.last_failures=[]
            try:
                for row in adapter.search(query,limit):
                    if isinstance(row,dict):
                        row=dict(row); row.setdefault('provider',adapter.name); result.append(row)
            except Exception as exc:
                failures.append({'provider':adapter.name,'error_type':type(exc).__name__})
            failures.extend({'provider':adapter.name,**item} for item in getattr(adapter,'last_failures',[]))
        self.last_failures=failures
        return result
def build_research_service(engine, *, tavily_enabled=False, environ=None):
    import os
    from .research import ResearchService
    env=os.environ if environ is None else environ
    from .integrations import IntegrationManager
    usage_manager=IntegrationManager(env,engine)
    adapters=[]
    if env.get('NEXUS_CROSSREF_ENABLED','true').lower()=='true': adapters.append(CrossrefDiscovery(usage_manager=usage_manager))
    if (tavily_enabled and env.get('NEXUS_TAVILY_AUTONOMOUS_APPROVED','false').lower()=='true'
            and env.get('TAVILY_API_KEY')):
        adapters.append(TavilyDiscovery(api_key=env['TAVILY_API_KEY'],usage_manager=usage_manager))
    discovery=adapters[0] if len(adapters)==1 else CompositeDiscovery(adapters)
    return ResearchService(engine,discovery)
