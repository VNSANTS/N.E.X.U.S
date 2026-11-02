"""Optional, budget-gated semantic index. Lexical retrieval remains the fallback."""
import json, math
from .engine import now

class SemanticMemoryIndex:
    def __init__(self,engine,embedder):
        self.engine,self.embedder=engine,embedder
        with engine.db() as c:
            c.executescript('''CREATE TABLE IF NOT EXISTS memory_embeddings(
              memory_id TEXT PRIMARY KEY REFERENCES memories(id) ON DELETE CASCADE,
              model TEXT NOT NULL,dimensions INTEGER NOT NULL,vector_json TEXT NOT NULL,updated_at TEXT NOT NULL);''')
    @staticmethod
    def _validate(vector):
        if not isinstance(vector,list) or not 1<=len(vector)<=4096: raise ValueError('invalid embedding vector')
        values=[float(x) for x in vector]
        if any(not math.isfinite(x) for x in values): raise ValueError('invalid embedding vector')
        return values
    def index(self,memory_id,*,task_id=None):
        if not callable(getattr(self.embedder,'embed',None)): return False
        with self.engine.db() as c:
            row=c.execute("SELECT title,body FROM memories WHERE id=? AND status='active'",(memory_id,)).fetchone()
        if not row: return False
        vector=self._validate(self.embedder.embed(row['title']+'\n'+row['body'],title=row['title'],task_type='RETRIEVAL_DOCUMENT',task_id=task_id))
        model=getattr(self.embedder,'model','unknown')
        with self.engine.db() as c:
            c.execute('INSERT INTO memory_embeddings VALUES(?,?,?,?,?) ON CONFLICT(memory_id) DO UPDATE SET model=excluded.model,dimensions=excluded.dimensions,vector_json=excluded.vector_json,updated_at=excluded.updated_at',(memory_id,model,len(vector),json.dumps(vector,separators=(',',':')),now()))
        return True
    def search(self,query,*,limit=5,task_id=None):
        if not callable(getattr(self.embedder,'embed',None)): return []
        with self.engine.db() as c:
            rows=c.execute("SELECT m.id,m.kind,m.title,m.body,e.dimensions,e.vector_json FROM memory_embeddings e JOIN memories m ON m.id=e.memory_id WHERE m.status='active'").fetchall()
        if not rows: return []
        query_vector=self._validate(self.embedder.embed(query,task_type='RETRIEVAL_QUERY',task_id=task_id))
        ranked=[]
        for row in rows:
            if row['dimensions']!=len(query_vector): continue
            vector=self._validate(json.loads(row['vector_json']))
            dot=sum(a*b for a,b in zip(query_vector,vector)); na=math.sqrt(sum(a*a for a in query_vector)); nb=math.sqrt(sum(b*b for b in vector))
            score=dot/(na*nb) if na and nb else 0
            if score>0.25: ranked.append((score,row))
        ranked.sort(key=lambda item:item[0],reverse=True)
        return [{'kind':'memory','id':row['id'],'score':score,'text':f"[{row['kind']} memory {row['id']}] {row['title']}: {row['body']}"} for score,row in ranked[:max(1,min(limit,20))]]
