"""Persistent fail-closed budget gate for remote model and embedding requests."""
import math
from datetime import datetime, timezone
from .engine import now, uid
from .providers.errors import ProviderConfigurationError, ProviderError

class ProviderBudgetExceededError(ProviderError):
    code='provider_budget_exceeded'
    safe_message='Provider usage budget is unavailable or exhausted.'

def estimate_text_tokens(text):
    """Conservative UTF-8 byte upper bound for text-only token budgeting."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return len(text.encode("utf-8"))


def estimate_message_tokens(messages):
    """Conservative text plus per-message framing allowance for chat requests."""
    if not isinstance(messages, (list, tuple)):
        raise TypeError("messages must be a list or tuple")
    total = 0
    for message in messages:
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ValueError("each message must contain string content")
        total += estimate_text_tokens(message["content"]) + 16
    return total


class ProviderBudget:
    def __init__(self,engine):
        self.engine=engine
        with engine.db() as c:
            c.executescript('''CREATE TABLE IF NOT EXISTS provider_budget_settings(
              id INTEGER PRIMARY KEY CHECK(id=1),enabled INTEGER NOT NULL DEFAULT 0,
              daily_calls INTEGER NOT NULL DEFAULT 0,daily_tokens INTEGER NOT NULL DEFAULT 0,
              daily_usd REAL NOT NULL DEFAULT 0,task_calls INTEGER NOT NULL DEFAULT 0,
              task_tokens INTEGER NOT NULL DEFAULT 0,task_usd REAL NOT NULL DEFAULT 0,
              input_usd_per_million REAL NOT NULL DEFAULT 0,output_usd_per_million REAL NOT NULL DEFAULT 0,
              updated_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS provider_usage(
              id TEXT PRIMARY KEY,task_id TEXT,provider TEXT NOT NULL,model TEXT NOT NULL,
              state TEXT NOT NULL,input_tokens INTEGER NOT NULL,output_tokens INTEGER NOT NULL,
              estimated_usd REAL NOT NULL,actual_usd REAL,created_at TEXT NOT NULL);
              CREATE INDEX IF NOT EXISTS idx_provider_usage_date ON provider_usage(created_at,task_id);
            ''')
            columns={r['name'] for r in c.execute('PRAGMA table_info(provider_budget_settings)')}
            for name in ('task_calls','task_tokens','task_usd'):
                if name not in columns: c.execute(f'ALTER TABLE provider_budget_settings ADD COLUMN {name} '+('REAL' if name=='task_usd' else 'INTEGER')+' NOT NULL DEFAULT 0')
            c.execute("INSERT OR IGNORE INTO provider_budget_settings(id,updated_at) VALUES(1,'')")
    def settings(self):
        with self.engine.db() as c: return dict(c.execute('SELECT * FROM provider_budget_settings WHERE id=1').fetchone())
    def update(self,*,enabled,daily_calls,daily_tokens,daily_usd,task_calls,task_tokens,task_usd,input_price,output_price):
        if not isinstance(enabled,bool): raise ValueError('enabled must be boolean')
        for value,low,high in ((daily_calls,0,10000),(daily_tokens,0,100_000_000),(task_calls,0,1000),(task_tokens,0,10_000_000)):
            if isinstance(value,bool) or not isinstance(value,int) or not low<=value<=high: raise ValueError('invalid usage limit')
        for value in (daily_usd,task_usd,input_price,output_price):
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=100000: raise ValueError('invalid price or budget')
        if enabled and (daily_calls<1 or daily_tokens<1 or daily_usd<=0 or task_calls<1 or task_tokens<1 or task_usd<=0): raise ValueError('enabled budget requires positive daily and per-task limits')
        if enabled and (input_price<=0 or output_price<=0): raise ValueError('enabled model budget requires explicit nonzero input and output rates')
        with self.engine.db() as c:
            c.execute('UPDATE provider_budget_settings SET enabled=?,daily_calls=?,daily_tokens=?,daily_usd=?,task_calls=?,task_tokens=?,task_usd=?,input_usd_per_million=?,output_usd_per_million=?,updated_at=? WHERE id=1',
              (int(enabled),daily_calls,daily_tokens,float(daily_usd),task_calls,task_tokens,float(task_usd),float(input_price),float(output_price),now()))
        return self.settings()
    def usage(self):
        today=datetime.now(timezone.utc).date().isoformat()+'%'
        with self.engine.db() as c:
            rows=[dict(r) for r in c.execute('SELECT provider,COUNT(*) calls,SUM(input_tokens+output_tokens) tokens,SUM(COALESCE(actual_usd,estimated_usd)) usd FROM provider_usage WHERE created_at LIKE ? GROUP BY provider',(today,)).fetchall()]
        return {'today':rows,'budget':self.settings()}
    def can_reserve(self,provider,input_tokens,output_tokens):
        """Read-only routing preflight; `_reserve` remains the atomic hard gate."""
        if any(isinstance(value,bool) or not isinstance(value,int) or value<0
               for value in (input_tokens,output_tokens)):
            return False
        cfg=self.settings()
        required=('daily_calls','daily_tokens','daily_usd','task_calls','task_tokens','task_usd')
        if not cfg['enabled'] or not all(cfg.get(key,0)>0 for key in required):
            return False
        if cfg.get('input_usd_per_million',0)<=0 or cfg.get('output_usd_per_million',0)<=0:
            return False
        estimate=(input_tokens*cfg['input_usd_per_million']+
                  output_tokens*cfg['output_usd_per_million'])/1_000_000
        today=datetime.now(timezone.utc).date().isoformat()+'%'
        with self.engine.db() as c:
            usage=c.execute("""SELECT COUNT(*) calls,
                COALESCE(SUM(input_tokens+output_tokens),0) tokens,
                COALESCE(SUM(COALESCE(actual_usd,estimated_usd)),0) usd
                FROM provider_usage WHERE created_at LIKE ?""",(today,)).fetchone()
        return (usage['calls']<cfg['daily_calls']
                and usage['tokens']+input_tokens+output_tokens<=cfg['daily_tokens']
                and usage['usd']+estimate<=cfg['daily_usd']
                and input_tokens+output_tokens<=cfg['task_tokens']
                and estimate<=cfg['task_usd'])
    def _reserve(self,provider,input_tokens,output_tokens,task_id):
        if any(isinstance(value,bool) or not isinstance(value,int) or value<0
               for value in (input_tokens,output_tokens)):
            raise ProviderConfigurationError()
        cfg=self.settings()
        if not cfg['enabled'] or not all(cfg[k]>0 for k in ('daily_usd','daily_calls','daily_tokens','task_usd','task_calls','task_tokens')):
            raise ProviderBudgetExceededError()
        if (not math.isfinite(cfg['input_usd_per_million'])
                or not math.isfinite(cfg['output_usd_per_million'])
                or cfg['input_usd_per_million']<=0
                or cfg['output_usd_per_million']<=0):
            raise ProviderConfigurationError()
        estimate=(input_tokens*cfg['input_usd_per_million']+output_tokens*cfg['output_usd_per_million'])/1_000_000
        if estimate<=0: estimate=1e-12
        usage_id=uid('usage'); stamp=now(); day=datetime.now(timezone.utc).date().isoformat()+'%'
        effective_task=task_id or usage_id
        with self.engine.db() as c:
            c.execute('BEGIN IMMEDIATE')
            daily=c.execute('SELECT COUNT(*) calls,COALESCE(SUM(input_tokens+output_tokens),0) tokens,COALESCE(SUM(COALESCE(actual_usd,estimated_usd)),0) usd FROM provider_usage WHERE created_at LIKE ?',(day,)).fetchone()
            task=c.execute('SELECT COUNT(*) calls,COALESCE(SUM(input_tokens+output_tokens),0) tokens,COALESCE(SUM(COALESCE(actual_usd,estimated_usd)),0) usd FROM provider_usage WHERE task_id=? AND created_at LIKE ?',(effective_task,day)).fetchone()
            if (daily['calls']+1>cfg['daily_calls'] or daily['tokens']+input_tokens+output_tokens>cfg['daily_tokens'] or daily['usd']+estimate>cfg['daily_usd']
                or task['calls']+1>cfg['task_calls'] or task['tokens']+input_tokens+output_tokens>cfg['task_tokens'] or task['usd']+estimate>cfg['task_usd']):
                raise ProviderBudgetExceededError()
            c.execute("INSERT INTO provider_usage VALUES(?,?,?,?, 'reserved',?,?,?,NULL,?)",
                (usage_id,effective_task,getattr(provider,'provider_name','unknown'),getattr(provider,'model','unknown'),input_tokens,output_tokens,estimate,stamp))
        return usage_id,cfg,input_tokens,output_tokens
    def _settle(self,usage_id,cfg,input_tokens,output_tokens,actual_in=None,actual_out=None,state='settled'):
        a=input_tokens if not isinstance(actual_in,int) or actual_in<0 else actual_in
        b=output_tokens if not isinstance(actual_out,int) or actual_out<0 else actual_out
        actual=(a*cfg['input_usd_per_million']+b*cfg['output_usd_per_million'])/1_000_000
        with self.engine.db() as c: c.execute('UPDATE provider_usage SET state=?,input_tokens=?,output_tokens=?,actual_usd=? WHERE id=?',(state,a,b,actual,usage_id))
    def generate(self,provider,messages,*,max_tokens=800,timeout=30,task_id=None):
        input_estimate=estimate_message_tokens(messages)
        output_estimate=max_tokens
        usage_id,cfg,input_estimate,output_estimate=self._reserve(provider,input_estimate,output_estimate,task_id)
        try: response=provider.generate(messages,max_tokens=max_tokens,timeout=timeout)
        except Exception:
            with self.engine.db() as c: c.execute("UPDATE provider_usage SET state='uncertain' WHERE id=?",(usage_id,))
            raise
        self._settle(usage_id,cfg,input_estimate,output_estimate,response.input_tokens,response.output_tokens)
        return response
    def embed(self,provider,text,*,title=None,task_type='RETRIEVAL_QUERY',timeout=30,task_id=None):
        if not callable(getattr(provider,'embed',None)): raise ProviderConfigurationError()
        estimated=estimate_text_tokens(text)
        usage_id,cfg,estimated,_=self._reserve(provider,estimated,0,task_id)
        try: vector=provider.embed(text,title=title,task_type=task_type,timeout=timeout)
        except Exception:
            with self.engine.db() as c: c.execute("UPDATE provider_usage SET state='uncertain' WHERE id=?",(usage_id,))
            raise
        self._settle(usage_id,cfg,estimated,0,estimated,0)
        return vector

class BudgetedProvider:
    supports_task_tracking=True
    def __init__(self,provider,budget): self.provider,self.budget=provider,budget
    @property
    def model(self): return getattr(self.provider,'model','unknown')
    @property
    def provider_name(self): return getattr(self.provider,'provider_name','unknown')
    def generate(self,messages,*,max_tokens=800,timeout=30,task_id=None):
        if self.provider_name=='mock': return self.provider.generate(messages,max_tokens=max_tokens,timeout=timeout)
        return self.budget.generate(self.provider,messages,max_tokens=max_tokens,timeout=timeout,task_id=task_id)
    def stream_generate(self,messages,*,max_tokens=800,timeout=60,task_id=None,cancel_event=None):
        stream=getattr(self.provider,'stream_generate',None)
        if not callable(stream): raise ProviderConfigurationError()
        estimated_input=sum(len(m['content']) for m in messages)
        usage_id,cfg,input_tokens,output_tokens=self.budget._reserve(
            self.provider,estimated_input,max_tokens,task_id)
        completed=False
        try:
            yield from stream(messages,max_tokens=max_tokens,timeout=timeout,cancel_event=cancel_event)
            completed=True
        except Exception:
            with self.budget.engine.db() as c:
                c.execute("UPDATE provider_usage SET state='uncertain' WHERE id=?",(usage_id,))
            raise
        finally:
            if completed:
                # Streaming endpoints do not consistently report token usage. The reserved
                # maximum is recorded as a conservative estimate rather than inventing counts.
                self.budget._settle(usage_id,cfg,input_tokens,output_tokens,state='estimated')
    def embed(self,text,*,title=None,task_type='RETRIEVAL_QUERY',timeout=30,task_id=None):
        return self.budget.embed(self.provider,text,title=title,task_type=task_type,timeout=timeout,task_id=task_id)
