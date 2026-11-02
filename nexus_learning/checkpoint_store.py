"""Durable, owner-scoped checkpoints for the specialist pipeline.

This store deliberately persists only bounded typed deliverables and hashes.
It does not execute providers or automatically retry ambiguous calls.
"""
import hashlib
import json
import re
import time

from .engine import now

STAGES = ("architect", "analyst", "reviewer")
RUN_STATES = {"pending", "running", "paused", "completed", "failed"}
STAGE_STATES = {"pending", "running", "completed", "failed_known", "interrupted_unknown"}
MAX_DELIVERABLE_BYTES = 8192
MAX_SUMMARY = 160
MAX_ITEM = 100
MAX_CLAIM = 50
MAX_NOTE = 80


class CheckpointError(ValueError):
    """Base class for safe checkpoint state errors."""


class CheckpointNotFound(CheckpointError):
    pass


class CheckpointConflict(CheckpointError):
    pass


class CheckpointStore:
    """SQLite checkpoint repository; every read and write is owner-scoped."""

    def __init__(self, engine):
        self.engine = engine
        with engine.db() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS agent_pipeline_runs (
              task_id TEXT PRIMARY KEY,
              owner_id TEXT NOT NULL,
              session_id TEXT NOT NULL,
              state TEXT NOT NULL,
              context_hash TEXT NOT NULL,
              provider_fingerprint TEXT NOT NULL,
              attempt INTEGER NOT NULL DEFAULT 1,
              lease_token TEXT,
              lease_expires REAL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_agent_pipeline_owner_state
              ON agent_pipeline_runs(owner_id,state,updated_at);
            CREATE TABLE IF NOT EXISTS agent_pipeline_stages (
              task_id TEXT NOT NULL REFERENCES agent_pipeline_runs(task_id) ON DELETE CASCADE,
              agent_id TEXT NOT NULL,
              sequence INTEGER NOT NULL,
              state TEXT NOT NULL,
              provider TEXT NOT NULL DEFAULT '',
              model TEXT NOT NULL DEFAULT '',
              input_hash TEXT NOT NULL DEFAULT '',
              deliverable_json TEXT,
              error_code TEXT,
              started_at TEXT,
              completed_at TEXT,
              PRIMARY KEY(task_id,agent_id)
            );
            CREATE INDEX IF NOT EXISTS idx_agent_pipeline_stage_state
              ON agent_pipeline_stages(task_id,state,sequence);
            CREATE TABLE IF NOT EXISTS agent_pipeline_attempts (
              task_id TEXT NOT NULL REFERENCES agent_pipeline_runs(task_id) ON DELETE CASCADE,
              attempt INTEGER NOT NULL,
              reason TEXT NOT NULL,
              created_at TEXT NOT NULL,
              PRIMARY KEY(task_id,attempt)
            );
            """)

    @staticmethod
    def digest(value):
        if not isinstance(value, str):
            raise CheckpointError("checkpoint hash input must be text")
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _json(value):
        if not isinstance(value, dict) or set(value) - {"summary", "items", "claims", "reviews"}:
            raise CheckpointError("invalid typed deliverable")
        summary = value.get("summary", "")
        items = value.get("items", [])
        claims = value.get("claims", [])
        reviews = value.get("reviews", [])
        if not isinstance(summary, str) or len(summary) > MAX_SUMMARY:
            raise CheckpointError("invalid deliverable summary")
        if not isinstance(items, list) or len(items) > 2 or any(
                not isinstance(item, str) or len(item) > MAX_ITEM for item in items):
            raise CheckpointError("invalid deliverable items")
        if not isinstance(claims, list) or len(claims) > 1:
            raise CheckpointError("invalid deliverable claims")
        clean_claims = []
        for claim in claims:
            if (not isinstance(claim, dict) or set(claim) - {"text", "evidence_ids", "link_status"}
                    or not isinstance(claim.get("text"), str)
                    or len(claim["text"]) > MAX_CLAIM
                    or not isinstance(claim.get("evidence_ids", []), list)
                    or len(claim.get("evidence_ids", [])) > 3
                    or any(not isinstance(x, str) or not re.fullmatch(r"S[1-3]", x)
                           for x in claim.get("evidence_ids", []))
                    or claim.get("link_status", "unreferenced") not in {"source_linked", "unreferenced"}):
                raise CheckpointError("invalid deliverable claim")
            clean_claims.append({"text": claim["text"],
                                 "evidence_ids": claim.get("evidence_ids", []),
                                 "link_status": claim.get("link_status", "unreferenced")})
        if not isinstance(reviews, list) or len(reviews) > 1:
            raise CheckpointError("invalid deliverable reviews")
        clean_reviews = []
        for review in reviews:
            if (not isinstance(review, dict) or set(review) - {"claim_index", "assessment", "note"}
                    or review.get("claim_index") != 0
                    or review.get("assessment") not in {"supported", "unsupported", "uncertain", "conflicting"}
                    or not isinstance(review.get("note", ""), str)
                    or len(review.get("note", "")) > MAX_NOTE):
                raise CheckpointError("invalid deliverable review")
            clean_reviews.append({"claim_index": 0, "assessment": review["assessment"],
                                  "note": review.get("note", "")})
        clean = {"summary": summary, "items": list(items),
                 "claims": clean_claims, "reviews": clean_reviews}
        encoded = json.dumps(clean, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > MAX_DELIVERABLE_BYTES:
            raise CheckpointError("checkpoint deliverable exceeds size limit")
        return encoded

    def create(self, task_id, owner_id, session_id, context_hash, provider_fingerprint):
        if (not all(isinstance(x, str) and x and len(x) <= 128
                    for x in (task_id, owner_id, session_id))
                or not isinstance(context_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", context_hash)
                or not isinstance(provider_fingerprint, str) or not provider_fingerprint
                or len(provider_fingerprint) > 512):
            raise CheckpointError("invalid checkpoint identity")
        stamp = now()
        with self.engine.db() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("""INSERT INTO agent_pipeline_runs
              (task_id,owner_id,session_id,state,context_hash,provider_fingerprint,created_at,updated_at)
              VALUES(?,?,?,'pending',?,?,?,?)""",
              (task_id, owner_id, session_id, context_hash, provider_fingerprint, stamp, stamp))
            c.executemany("""INSERT INTO agent_pipeline_stages
              (task_id,agent_id,sequence,state) VALUES(?,?,?,'pending')""",
              [(task_id, name, index) for index, name in enumerate(STAGES)])
        return self.get(task_id, owner_id)

    def get(self, task_id, owner_id):
        with self.engine.db() as c:
            run = c.execute("SELECT * FROM agent_pipeline_runs WHERE task_id=? AND owner_id=?",
                            (task_id, owner_id)).fetchone()
            if not run:
                return None
            result = dict(run)
            result.pop("lease_token", None)
            result.pop("lease_expires", None)
            result["stages"] = [dict(row) for row in c.execute(
                "SELECT agent_id,sequence,state,provider,model,input_hash,deliverable_json,error_code,started_at,completed_at "
                "FROM agent_pipeline_stages WHERE task_id=? ORDER BY sequence", (task_id,))]
            return result

    def acquire(self, task_id, owner_id, session_id, *, lease_seconds=120):
        """Acquire a resume lease; stale running stages become unknown, never pending."""
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int) or not 10 <= lease_seconds <= 600:
            raise CheckpointError("invalid lease duration")
        token = hashlib.sha256(f"{task_id}:{owner_id}:{time.time_ns()}".encode()).hexdigest()
        with self.engine.db() as c:
            c.execute("BEGIN IMMEDIATE")
            run = c.execute("SELECT * FROM agent_pipeline_runs WHERE task_id=? AND owner_id=? AND session_id=?",
                            (task_id, owner_id, session_id)).fetchone()
            if not run:
                raise CheckpointNotFound("checkpoint not found")
            if run["state"] == "completed":
                raise CheckpointConflict("pipeline already completed")
            if run["lease_token"] and (run["lease_expires"] or 0) > time.time():
                raise CheckpointConflict("pipeline is already leased")
            c.execute("""UPDATE agent_pipeline_stages SET state='interrupted_unknown',
                       error_code='process_interrupted'
                       WHERE task_id=? AND state='running'""", (task_id,))
            c.execute("""UPDATE agent_pipeline_runs SET state='paused',lease_token=?,lease_expires=?,
                       updated_at=? WHERE task_id=?""",
                      (token, time.time() + lease_seconds, now(), task_id))
            unknown = c.execute("""SELECT agent_id FROM agent_pipeline_stages
                                   WHERE task_id=? AND state='interrupted_unknown'
                                   ORDER BY sequence""", (task_id,)).fetchall()
            return {"lease_token": token, "ambiguous_stages": [r["agent_id"] for r in unknown]}

    def start_stage(self, task_id, owner_id, lease_token, agent_id, provider, model, input_hash):
        if agent_id not in STAGES or not all(isinstance(x, str) and len(x) <= 256
                                             for x in (provider, model, input_hash)):
            raise CheckpointError("invalid stage metadata")
        with self.engine.db() as c:
            c.execute("BEGIN IMMEDIATE")
            run = c.execute("""SELECT state,lease_token,lease_expires FROM agent_pipeline_runs
                               WHERE task_id=? AND owner_id=?""", (task_id, owner_id)).fetchone()
            if not run or run["lease_token"] != lease_token or (run["lease_expires"] or 0) <= time.time():
                raise CheckpointConflict("lease is not valid")
            prior = c.execute("SELECT state,sequence FROM agent_pipeline_stages WHERE task_id=? AND agent_id=?",
                              (task_id, agent_id)).fetchone()
            if not prior or prior["state"] != "pending":
                raise CheckpointConflict("stage is not pending; ambiguous stages require explicit resolution")
            earlier = c.execute("""SELECT COUNT(*) FROM agent_pipeline_stages
                WHERE task_id=? AND sequence<? AND state!='completed'""",
                (task_id, prior["sequence"])).fetchone()[0]
            if earlier:
                raise CheckpointConflict("earlier stages must be completed first")
            stamp = now()
            c.execute("""UPDATE agent_pipeline_stages SET state='running',provider=?,model=?,
                       input_hash=?,started_at=?,completed_at=NULL,error_code=NULL
                       WHERE task_id=? AND agent_id=? AND state='pending'""",
                      (provider[:64], model[:128], input_hash, stamp, task_id, agent_id))
            c.execute("UPDATE agent_pipeline_runs SET state='running',updated_at=? WHERE task_id=?",
                      (stamp, task_id))

    def complete_stage(self, task_id, owner_id, lease_token, agent_id, deliverable):
        encoded = self._json(deliverable)
        with self.engine.db() as c:
            c.execute("BEGIN IMMEDIATE")
            run = c.execute("SELECT lease_token,lease_expires FROM agent_pipeline_runs WHERE task_id=? AND owner_id=?",
                            (task_id, owner_id)).fetchone()
            if not run or run["lease_token"] != lease_token or (run["lease_expires"] or 0) <= time.time():
                raise CheckpointConflict("lease is not valid")
            cur = c.execute("""UPDATE agent_pipeline_stages SET state='completed',deliverable_json=?,
                       completed_at=?,error_code=NULL WHERE task_id=? AND agent_id=? AND state='running'""",
                            (encoded, now(), task_id, agent_id))
            if cur.rowcount != 1:
                raise CheckpointConflict("stage is not running")
            remaining = c.execute("""SELECT COUNT(*) FROM agent_pipeline_stages
                WHERE task_id=? AND state!='completed'""", (task_id,)).fetchone()[0]
            c.execute("UPDATE agent_pipeline_runs SET state=?,updated_at=? WHERE task_id=?",
                      ("completed" if remaining == 0 else "running", now(), task_id))

    def fail_stage(self, task_id, owner_id, lease_token, agent_id, *, ambiguous=False):
        state = "interrupted_unknown" if ambiguous else "failed_known"
        code = "provider_outcome_unknown" if ambiguous else "stage_failed"
        with self.engine.db() as c:
            c.execute("BEGIN IMMEDIATE")
            run = c.execute("SELECT lease_token,lease_expires FROM agent_pipeline_runs WHERE task_id=? AND owner_id=?",
                            (task_id, owner_id)).fetchone()
            if not run or run["lease_token"] != lease_token or (run["lease_expires"] or 0) <= time.time():
                raise CheckpointConflict("lease is not valid")
            cur = c.execute("""UPDATE agent_pipeline_stages SET state=?,error_code=?,completed_at=?
                       WHERE task_id=? AND agent_id=? AND state='running'""",
                            (state, code, now(), task_id, agent_id))
            if cur.rowcount != 1:
                raise CheckpointConflict("stage is not running")
            c.execute("UPDATE agent_pipeline_runs SET state='paused',updated_at=? WHERE task_id=?",
                      (now(), task_id))

    def release(self, task_id, owner_id, lease_token):
        with self.engine.db() as c:
            c.execute("BEGIN IMMEDIATE")
            cur = c.execute("""UPDATE agent_pipeline_runs SET lease_token=NULL,lease_expires=NULL,
                       state=CASE WHEN state='running' THEN 'paused' ELSE state END,updated_at=?
                       WHERE task_id=? AND owner_id=? AND lease_token=?""",
                            (now(), task_id, owner_id, lease_token))
            if cur.rowcount != 1:
                raise CheckpointConflict("lease is not valid")
