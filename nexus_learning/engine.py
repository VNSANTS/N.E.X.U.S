import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import uuid

def now():
    return datetime.now(timezone.utc).isoformat()

class LearningEngine:
    """Minimal SQLite memory and evidence store."""
    def __init__(self, path="nexus_learning.db"):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.db() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS memories(
              id TEXT PRIMARY KEY, kind TEXT, title TEXT, body TEXT,
              created_at TEXT, status TEXT DEFAULT 'active');
            CREATE TABLE IF NOT EXISTS sources(
              id TEXT PRIMARY KEY, uri TEXT, title TEXT, retrieved_at TEXT);
            CREATE TABLE IF NOT EXISTS claims(
              id TEXT PRIMARY KEY, claim TEXT, state TEXT, rationale TEXT,
              confidence REAL, created_at TEXT);
            CREATE TABLE IF NOT EXISTS claim_sources(
              claim_id TEXT, source_id TEXT, excerpt TEXT,
              FOREIGN KEY(claim_id) REFERENCES claims(id),
              FOREIGN KEY(source_id) REFERENCES sources(id));
            CREATE TABLE IF NOT EXISTS tasks(
              id TEXT PRIMARY KEY, title TEXT, relevance REAL, uncertainty REAL,
              impact REAL, novelty REAL, cost REAL, sensitivity REAL,
              status TEXT DEFAULT 'pending', created_at TEXT);
            """)
    def db(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        return c
    def add_memory(self, kind, title, body):
        if kind not in {"episodic", "semantic", "procedural"}:
            raise ValueError("invalid memory kind")
        mid = uuid.uuid4().hex
        with self.db() as c:
            c.execute("INSERT INTO memories VALUES(?,?,?,?,?,'active')",
                      (mid, kind, title, body, now()))
        return mid
    def add_source(self, uri, title=""):
        sid = uuid.uuid4().hex
        with self.db() as c:
            c.execute("INSERT INTO sources VALUES(?,?,?,?)", (sid, uri, title, now()))
        return sid
    def propose_claim(self, claim, source_ids=()):
        cid = uuid.uuid4().hex
        with self.db() as c:
            c.execute("INSERT INTO claims VALUES(?,?,'proposed',NULL,NULL,?)",
                      (cid, claim, now()))
            for sid in source_ids:
                if not c.execute("SELECT 1 FROM sources WHERE id=?", (sid,)).fetchone():
                    raise ValueError("unknown source")
                c.execute("INSERT INTO claim_sources VALUES(?,?,NULL)", (cid, sid))
        return cid
    def review_claim(self, claim_id, state, rationale, confidence=None):
        allowed = {"proposed", "under_review", "validated", "disputed", "stale", "rejected"}
        if state not in allowed or not rationale.strip():
            raise ValueError("invalid state or missing rationale")
        if confidence is not None and not 0 <= confidence <= 1:
            raise ValueError("confidence must be from 0 to 1")
        if state == "validated" and confidence is None:
            raise ValueError("validation requires explicit confidence")
        with self.db() as c:
            cur = c.execute("UPDATE claims SET state=?,rationale=?,confidence=? WHERE id=?",
                            (state, rationale, confidence, claim_id))
            if cur.rowcount != 1:
                raise KeyError(claim_id)
    def add_task(self, title, relevance=0, uncertainty=0, impact=0,
                 novelty=0, cost=0, sensitivity=0):
        values = (relevance, uncertainty, impact, novelty, cost, sensitivity)
        if any(not 0 <= v <= 1 for v in values):
            raise ValueError("priority inputs must be from 0 to 1")
        tid = uuid.uuid4().hex
        with self.db() as c:
            c.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?, 'pending',?)",
                      (tid, title, *values, now()))
        return tid
    def prioritized_tasks(self):
        with self.db() as c:
            rows = [dict(r) for r in c.execute(
                "SELECT * FROM tasks WHERE status='pending'").fetchall()]
        for r in rows:
            r["score"] = round(.25*r["relevance"] + .2*r["uncertainty"] +
                .2*r["impact"] + .15*r["novelty"] - .1*r["cost"] -
                .1*r["sensitivity"], 4)
        return sorted(rows, key=lambda r: r["score"], reverse=True)
