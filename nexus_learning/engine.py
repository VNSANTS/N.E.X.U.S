"""Auditable, local-first learning core for N.E.X.U.S. (standard library only)."""
import json
import sqlite3
import uuid
import math
from urllib.parse import urlsplit
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

MEMORY_TYPES = {"episodic", "semantic", "procedural"}
CLAIM_STATES = {"proposed", "under_review", "validated", "disputed", "stale", "rejected"}
TASK_STATES = {"pending", "in_progress", "done", "blocked", "cancelled"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def uid(prefix):
    return prefix + "_" + uuid.uuid4().hex


class LearningEngine:
    """SQLite store for memories, sourced claims, review states and learning tasks.

    This module does not browse, call an LLM, or autonomously validate claims.
    """

    def __init__(self, path="nexus_learning.db"):
        self.path = str(path)
        self._sqlite_uri = self.path == ":memory:"
        self._database = (
            f"file:nexus_{uuid.uuid4().hex}?mode=memory&cache=shared"
            if self._sqlite_uri else self.path
        )
        # Keep one anchor connection alive so shared in-memory SQLite databases
        # survive between the short-lived connections opened by db().
        self._keeper = (
            sqlite3.connect(self._database, uri=True, check_same_thread=False, timeout=10)
            if self._sqlite_uri else None
        )
        if not self._sqlite_uri:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.db() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS memories(
              id TEXT PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL,
              body TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'active', metadata TEXT NOT NULL DEFAULT '{}');
            CREATE TABLE IF NOT EXISTS sources(
              id TEXT PRIMARY KEY, uri TEXT NOT NULL, title TEXT NOT NULL DEFAULT '',
              retrieved_at TEXT NOT NULL, metadata TEXT NOT NULL DEFAULT '{}');
            CREATE TABLE IF NOT EXISTS claims(
              id TEXT PRIMARY KEY, claim TEXT NOT NULL, state TEXT NOT NULL,
              rationale TEXT, confidence REAL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS claim_sources(
              claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
              source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
              excerpt TEXT, PRIMARY KEY(claim_id, source_id));
            CREATE TABLE IF NOT EXISTS tasks(
              id TEXT PRIMARY KEY, title TEXT NOT NULL, relevance REAL NOT NULL,
              uncertainty REAL NOT NULL, impact REAL NOT NULL, novelty REAL NOT NULL,
              cost REAL NOT NULL, sensitivity REAL NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit_log(
              id TEXT PRIMARY KEY, event TEXT NOT NULL, entity_type TEXT NOT NULL,
              entity_id TEXT NOT NULL, details TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_memory_kind ON memories(kind, status);
            CREATE INDEX IF NOT EXISTS idx_claim_state ON claims(state);
            CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status);
            """)
    @contextmanager
    def db(self):
        c = sqlite3.connect(self._database, uri=self._sqlite_uri, timeout=10)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    def close(self):
        """Close the anchor connection for an in-memory database, if present."""
        if self._keeper is not None:
            self._keeper.close()
            self._keeper = None

    @staticmethod
    def _metadata(value):
        if value is None:
            value = {}
        if not isinstance(value, dict):
            raise ValueError("metadata must be an object")
        try:
            encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
        except (TypeError, ValueError):
            raise ValueError("metadata must contain finite JSON-compatible values") from None
        if len(encoded.encode("utf-8")) > 8192:
            raise ValueError("metadata exceeds 8 KiB")
        return encoded

    def _audit(self, c, event, kind, entity_id, details=None):
        c.execute("INSERT INTO audit_log VALUES(?,?,?,?,?,?)",
                  (uid("evt"), event, kind, entity_id, self._metadata(details), now()))

    def add_memory(self, kind, title, body, metadata=None):
        if kind not in MEMORY_TYPES:
            raise ValueError("invalid memory kind")
        if not isinstance(title, str) or not isinstance(body, str):
            raise ValueError("title and body must be text")
        if not title.strip() or not body.strip():
            raise ValueError("title and body cannot be empty")
        if len(title) > 500 or len(body) > 12_000:
            raise ValueError("memory title or body exceeds the allowed size")
        metadata_json = self._metadata(metadata)
        mid, stamp = uid("mem"), now()
        with self.db() as c:
            c.execute("INSERT INTO memories VALUES(?,?,?,?,?,?, 'active',?)",
                      (mid, kind, title.strip(), body.strip(), stamp, stamp, metadata_json))
            self._audit(c, "memory.created", "memory", mid, {"kind": kind})
        return mid

    def search_memories(self, query="", memory_type=None, limit=50):
        if not isinstance(query, str):
            raise ValueError("query must be text")
        if memory_type is not None and memory_type not in MEMORY_TYPES:
            raise ValueError("invalid memory type")
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ValueError("limit must be an integer")
        sql, args = "SELECT * FROM memories WHERE status='active'", []
        if memory_type:
            sql += " AND kind=?"
            args.append(memory_type)
        if query.strip():
            sql += " AND (title LIKE ? OR body LIKE ?)"
            args += ["%" + query.strip() + "%"] * 2
        sql += " ORDER BY updated_at DESC LIMIT ?"
        args.append(max(1, min(int(limit), 200)))
        with self.db() as c:
            return [dict(r) for r in c.execute(sql, args).fetchall()]

    def archive_memory(self, memory_id):
        with self.db() as c:
            cur = c.execute("UPDATE memories SET status='archived',updated_at=? WHERE id=? AND status='active'",
                            (now(), memory_id))
            if cur.rowcount:
                self._audit(c, "memory.archived", "memory", memory_id)
            return cur.rowcount == 1

    def add_source(self, uri, title=""):
        if not uri.strip():
            raise ValueError("source URI cannot be empty")
        sid = uid("src")
        with self.db() as c:
            c.execute("INSERT INTO sources VALUES(?,?,?,?,?)",
                      (sid, uri.strip(), title.strip(), now(), "{}"))
            self._audit(c, "source.added", "source", sid, {"uri": uri.strip()})
        return sid

    def propose_claim(self, claim, source_ids=(), excerpts=None):
        if not isinstance(claim, str) or not claim.strip():
            raise ValueError("claim cannot be empty")
        if not isinstance(source_ids, (list, tuple)):
            raise ValueError("source_ids must be a list")
        if excerpts is not None and not isinstance(excerpts, dict):
            raise ValueError("excerpts must be an object")
        cid, stamp = uid("claim"), now()
        source_ids = list(dict.fromkeys(source_ids))
        if not all(isinstance(sid, str) and sid for sid in source_ids):
            raise ValueError("source IDs must be non-empty strings")
        if excerpts and any(key not in source_ids or not isinstance(value, str)
                            for key, value in excerpts.items()):
            raise ValueError("excerpts must reference linked sources and contain text")
        with self.db() as c:
            for sid in source_ids:
                if not c.execute("SELECT 1 FROM sources WHERE id=?", (sid,)).fetchone():
                    raise ValueError("unknown source: " + sid)
            c.execute("INSERT INTO claims VALUES(?,?,'proposed',NULL,NULL,?,?)",
                      (cid, claim.strip(), stamp, stamp))
            for sid in source_ids:
                excerpt = (excerpts or {}).get(sid)
                c.execute("INSERT INTO claim_sources VALUES(?,?,?)",
                          (cid, sid, excerpt.strip() if isinstance(excerpt, str) and excerpt.strip() else None))
            self._audit(c, "claim.proposed", "claim", cid, {"source_count": len(source_ids)})
        return cid

    def assess_claim_evidence(self, claim_id):
        """Return deterministic provenance/completeness checks, never semantic proof."""
        with self.db() as c:
            claim = c.execute("SELECT id FROM claims WHERE id=?", (claim_id,)).fetchone()
            if not claim:
                raise KeyError(claim_id)
            rows = [dict(row) for row in c.execute("""
                SELECT s.id,s.uri,s.title,cs.excerpt FROM claim_sources cs
                JOIN sources s ON s.id=cs.source_id WHERE cs.claim_id=? ORDER BY s.id
            """, (claim_id,)).fetchall()]
        valid_sources, excerpt_count = 0, 0
        domains, issues = set(), []
        for source in rows:
            try:
                parsed = urlsplit(source["uri"])
                valid_url = parsed.scheme in {"http", "https"} and bool(parsed.hostname)
            except (TypeError, ValueError):
                valid_url = False
                parsed = None
            if valid_url:
                valid_sources += 1
                domains.add((parsed.hostname or "").lower().removeprefix("www."))
            else:
                issues.append("source_url_not_http")
            if isinstance(source.get("excerpt"), str) and source["excerpt"].strip():
                excerpt_count += 1
            else:
                issues.append("missing_source_excerpt")
        if not rows:
            issues.append("no_linked_sources")
        if rows and len(domains) < 2:
            issues.append("single_domain")
        complete = bool(rows) and valid_sources == len(rows) and excerpt_count == len(rows)
        return {"claim_id": claim_id, "source_count": len(rows),
                "valid_source_count": valid_sources, "excerpt_count": excerpt_count,
                "distinct_domains": len(domains), "complete": complete,
                "issues": sorted(set(issues)),
                "limitation": "Completeness checks do not establish that an excerpt semantically supports the claim.",
                "sources": rows}

    def review_claim(self, claim_id, state, rationale, confidence=None):
        if state not in CLAIM_STATES or not isinstance(rationale, str) or not rationale.strip():
            raise ValueError("invalid state or missing rationale")
        if confidence is not None and (isinstance(confidence, bool)
                or not isinstance(confidence, (int, float)) or not math.isfinite(confidence)
                or not 0 <= confidence <= 1):
            raise ValueError("confidence must be between 0 and 1")
        if state == "validated" and confidence is None:
            raise ValueError("validated claims require explicit confidence")
        with self.db() as c:
            if not c.execute("SELECT 1 FROM claims WHERE id=?", (claim_id,)).fetchone():
                raise KeyError(claim_id)
            if state == "validated":
                evidence = self.assess_claim_evidence(claim_id)
                if not evidence["complete"]:
                    raise ValueError("validated claims require HTTP(S) sources and a non-empty excerpt for every source")
            cur = c.execute("UPDATE claims SET state=?,rationale=?,confidence=?,updated_at=? WHERE id=?",
                            (state, rationale.strip(), confidence, now(), claim_id))
            if cur.rowcount != 1:
                raise KeyError(claim_id)
            self._audit(c, "claim.reviewed", "claim", claim_id,
                        {"state": state, "confidence": confidence, "rationale": rationale.strip()})

    def get_claim(self, claim_id):
        with self.db() as c:
            row = c.execute("SELECT * FROM claims WHERE id=?", (claim_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            result["sources"] = [dict(r) for r in c.execute("""
              SELECT s.id,s.uri,s.title,cs.excerpt FROM claim_sources cs
              JOIN sources s ON s.id=cs.source_id WHERE cs.claim_id=?""", (claim_id,))]
        result["evidence_quality"] = self.assess_claim_evidence(claim_id)
        return result

    def list_claims(self, state=None, limit=100):
        if state is not None and state not in CLAIM_STATES:
            raise ValueError("invalid claim state")
        sql, args = "SELECT * FROM claims", []
        if state:
            sql += " WHERE state=?"
            args.append(state)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        args.append(max(1, min(int(limit), 500)))
        with self.db() as c:
            ids = [r["id"] for r in c.execute(sql, args).fetchall()]
        return [self.get_claim(claim_id) for claim_id in ids]

    def add_task(self, title, relevance=0, uncertainty=0, impact=0,
                 novelty=0, cost=0, sensitivity=0):
        vals = (relevance, uncertainty, impact, novelty, cost, sensitivity)
        if not title.strip() or any(not 0 <= float(v) <= 1 for v in vals):
            raise ValueError("title required and priority dimensions must be from 0 to 1")
        tid, stamp = uid("task"), now()
        with self.db() as c:
            c.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?, 'pending',?,?)",
                      (tid, title.strip(), *vals, stamp, stamp))
            self._audit(c, "task.created", "task", tid)
        return tid

    @staticmethod
    def priority_score(task):
        return round(.25*task["relevance"] + .20*task["uncertainty"] +
                     .20*task["impact"] + .15*task["novelty"] -
                     .10*task["cost"] - .10*task["sensitivity"], 4)

    def prioritized_tasks(self, limit=50):
        with self.db() as c:
            rows = [dict(r) for r in c.execute(
                "SELECT * FROM tasks WHERE status='pending'").fetchall()]
        for row in rows:
            row["score"] = self.priority_score(row)
        rows.sort(key=lambda row: (row["score"], row["created_at"]), reverse=True)
        return rows[:max(1, min(int(limit), 200))]

    def set_task_status(self, task_id, status):
        if status not in TASK_STATES:
            raise ValueError("invalid task status")
        with self.db() as c:
            cur = c.execute("UPDATE tasks SET status=?,updated_at=? WHERE id=?",
                            (status, now(), task_id))
            if cur.rowcount != 1:
                raise KeyError(task_id)
            self._audit(c, "task.status_changed", "task", task_id, {"status": status})

    def consolidation_report(self):
        """Return review candidates only; never changes or validates stored knowledge."""
        memories = self.search_memories(limit=200)
        claims = self.list_claims(limit=500)
        normalized = {}
        for claim in claims:
            key = " ".join(claim["claim"].lower().split()).strip(" .!?")
            normalized.setdefault(key, []).append(claim)
        duplicates = [group for group in normalized.values() if len(group) > 1]
        return {
            "generated_at": now(),
            "memory_count": len(memories),
            "claim_count": len(claims),
            "claims_without_sources": [c["id"] for c in claims if not self.get_claim(c["id"])["sources"]],
            "possible_duplicate_claim_groups": [[c["id"] for c in group] for group in duplicates],
            "disputed_claims": [c["id"] for c in claims if c["state"] == "disputed"],
            "unreviewed_claims": [c["id"] for c in claims if c["state"] in {"proposed", "under_review"}],
            "note": "Report only. No automatic promotion, deletion or overwrite was performed."
        }

    def audit_events(self, limit=100):
        with self.db() as c:
            return [dict(r) for r in c.execute(
                "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?",
                (max(1, min(int(limit), 500)),)).fetchall()]

    def stats(self):
        with self.db() as c:
            return {
                "memories": c.execute("SELECT COUNT(*) FROM memories WHERE status='active'").fetchone()[0],
                "sources": c.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
                "claims": c.execute("SELECT COUNT(*) FROM claims").fetchone()[0],
                "tasks_pending": c.execute("SELECT COUNT(*) FROM tasks WHERE status='pending'").fetchone()[0]
            }
