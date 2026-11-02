"""Owner-approved, text-only runtime skills with on-demand loading."""
from dataclasses import dataclass
import hashlib
import json
import re
from .engine import now, uid


@dataclass(frozen=True)
class Skill:
    name: str
    version: str
    description: str
    instructions: str
    tools: tuple = ()


class SkillRegistry:
    MAX_INSTRUCTIONS = 12000
    def __init__(self, engine):
        self.engine = engine
        with engine.db() as c:
            c.executescript("""CREATE TABLE IF NOT EXISTS runtime_skills(
                id TEXT PRIMARY KEY,name TEXT NOT NULL,version TEXT NOT NULL,
                description TEXT NOT NULL,instructions TEXT NOT NULL,
                tool_allowlist TEXT NOT NULL,status TEXT NOT NULL,
                content_hash TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,
                UNIQUE(name,version));
                CREATE TABLE IF NOT EXISTS runtime_skill_events(
                id TEXT PRIMARY KEY,skill_id TEXT NOT NULL,event TEXT NOT NULL,
                owner_id TEXT NOT NULL,created_at TEXT NOT NULL);""")

    def propose(self, name, version, description, instructions, tools=()):
        self._validate(name, version, description, instructions, tools)
        sid, stamp = uid("skill"), now()
        digest = hashlib.sha256(instructions.encode("utf-8")).hexdigest()
        with self.engine.db() as c:
            c.execute("INSERT INTO runtime_skills VALUES(?,?,?,?,?,?,'proposed',?,?,?)",
                (sid,name,version,description,instructions,json.dumps(list(tools)),digest,stamp,stamp))
        return sid

    def approve(self, skill_id, *, owner_id, approved):
        if approved is not True: raise PermissionError("explicit approval required")
        with self.engine.db() as c:
            c.execute("BEGIN IMMEDIATE")
            changed=c.execute("UPDATE runtime_skills SET status='approved',updated_at=? WHERE id=? AND status='proposed'",
                              (now(),skill_id))
            if not changed.rowcount: raise KeyError(skill_id)
            c.execute("INSERT INTO runtime_skill_events VALUES(?,?,?,?,?)",
                      (uid("ske"),skill_id,"approved",owner_id,now()))

    def discover(self, query="", limit=20):
        if not isinstance(query,str) or len(query)>300: raise ValueError("invalid skill query")
        limit=max(1,min(int(limit),50)); pattern="%"+query.strip()+"%"
        with self.engine.db() as c:
            rows=c.execute("SELECT name,version,description,status FROM runtime_skills WHERE status='approved' AND (name LIKE ? OR description LIKE ?) ORDER BY name,created_at DESC LIMIT ?",
                           (pattern,pattern,limit*3)).fetchall()
        seen=set(); unique=[]
        for row in rows:
            if row["name"] not in seen:
                seen.add(row["name"]); unique.append(dict(row))
            if len(unique)>=limit: break
        return unique

    def select_for_message(self, message, *, owner_id, max_skills=2, max_chars=5000):
        if not isinstance(message,str) or not message.strip(): return []
        terms={w.lower() for w in re.findall(r"[\w-]{3,}",message,flags=re.UNICODE)}
        with self.engine.db() as c:
            rows=c.execute("SELECT name,description FROM runtime_skills WHERE status='approved'").fetchall()
        candidates=[]
        for row in rows:
            tokens={w.lower() for w in re.findall(r"[\w-]{3,}",row["name"].replace("-"," ")+" "+row["description"],flags=re.UNICODE)}
            score=len(terms & tokens)
            if score: candidates.append((-score,row["name"]))
        selected=[]; used=0
        for _,name in sorted(candidates)[:max_skills]:
            skill=self.load(name,owner_id=owner_id)
            remaining=max_chars-used
            if remaining<=0: break
            skill["instructions"]=skill["instructions"][:remaining]
            used+=len(skill["instructions"])
            selected.append(skill)
        return selected

    def load(self, name, *, owner_id):
        with self.engine.db() as c:
            row=c.execute("SELECT * FROM runtime_skills WHERE name=? AND status='approved' ORDER BY created_at DESC LIMIT 1",(name,)).fetchone()
            if not row: raise KeyError(name)
            if hashlib.sha256(row["instructions"].encode("utf-8")).hexdigest()!=row["content_hash"]:
                raise ValueError("skill integrity validation failed")
            c.execute("INSERT INTO runtime_skill_events VALUES(?,?,?,?,?)",
                      (uid("ske"),row["id"],"loaded",owner_id,now()))
        return {"name":row["name"],"version":row["version"],"description":row["description"],
                "instructions":row["instructions"],"tools":json.loads(row["tool_allowlist"])}

    @classmethod
    def _validate(cls,name,version,description,instructions,tools):
        if not isinstance(name,str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,63}",name): raise ValueError("invalid skill name")
        if not isinstance(version,str) or not re.fullmatch(r"\d+\.\d+\.\d+",version): raise ValueError("invalid skill version")
        if not isinstance(description,str) or not description.strip() or len(description)>500: raise ValueError("invalid skill description")
        if not isinstance(instructions,str) or not instructions.strip() or len(instructions)>cls.MAX_INSTRUCTIONS: raise ValueError("invalid skill instructions")
        if not isinstance(tools,(tuple,list)) or any(not isinstance(t,str) or not re.fullmatch(r"[a-z][a-z0-9_.-]{1,80}",t) for t in tools): raise ValueError("invalid skill tools")
        if tools: raise ValueError("runtime skills cannot grant tools; use the independently authorized registry")
