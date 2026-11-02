"""Durable local job queue with leases, idempotency and bounded retries."""
import json
import secrets
import threading
from datetime import datetime, timedelta, timezone

from .engine import now, uid


class TaskQueue:
    def __init__(self, engine, *, max_attempts=3, lease_seconds=60):
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= 10:
            raise ValueError("max_attempts must be between 1 and 10")
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int) or not 1 <= lease_seconds <= 3600:
            raise ValueError("lease_seconds must be between 1 and 3600")
        self.engine = engine
        self.max_attempts = max_attempts
        self.lease_seconds = lease_seconds
        self._enqueue_lock = threading.Lock()
        with engine.db() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS worker_jobs(
              id TEXT PRIMARY KEY,owner_id TEXT,kind TEXT NOT NULL,payload TEXT NOT NULL,priority INTEGER NOT NULL,
              idempotency_key TEXT,state TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,
              max_attempts INTEGER NOT NULL,lease_until TEXT,lease_token TEXT,run_after TEXT NOT NULL,
              result TEXT,error_code TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,
              UNIQUE(owner_id,idempotency_key));
            CREATE INDEX IF NOT EXISTS idx_worker_jobs_due ON worker_jobs(state,run_after,priority);
            CREATE TABLE IF NOT EXISTS worker_job_events(
              id TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES worker_jobs(id),event TEXT NOT NULL,
              details TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS worker_instances(
              id TEXT PRIMARY KEY,state TEXT NOT NULL,started_at TEXT NOT NULL,heartbeat_at TEXT NOT NULL);
            """)

    def enqueue(self, kind, payload=None, *, owner_id=None, priority=0, idempotency_key=None, run_after=None):
        if kind not in {"memory.consolidate", "learning.stats", "learning.cycle_step"}:
            raise ValueError("job kind is not allowlisted")
        payload = payload or {}
        if not isinstance(payload, dict) or len(json.dumps(payload)) > 8192:
            raise ValueError("payload must be a small JSON object")
        if not isinstance(priority, int) or isinstance(priority, bool) or not -100 <= priority <= 100:
            raise ValueError("priority must be between -100 and 100")
        if idempotency_key is not None and (not isinstance(idempotency_key, str) or not idempotency_key or len(idempotency_key) > 128):
            raise ValueError("invalid idempotency key")
        if owner_id is not None and (not isinstance(owner_id, str) or len(owner_id) > 128):
            raise ValueError("invalid owner id")
        if run_after is not None:
            try:
                parsed = datetime.fromisoformat(run_after.replace("Z", "+00:00"))
            except (AttributeError, ValueError):
                raise ValueError("run_after must be an ISO-8601 timestamp") from None
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            run_after = parsed.astimezone(timezone.utc).isoformat(timespec="seconds")
        stamp, job_id = now(), uid("job")
        with self._enqueue_lock:
            with self.engine.db() as c:
                # Serialize the lookup and insert across queue instances/processes.
                # The Python lock also avoids SQLITE_LOCKED from SQLite shared-cache
                # databases used by in-memory tests.
                c.execute("BEGIN IMMEDIATE")
                if idempotency_key:
                    existing = c.execute("SELECT id FROM worker_jobs WHERE idempotency_key=? AND owner_id IS ?",
                                         (idempotency_key, owner_id)).fetchone()
                    if existing:
                        return existing["id"]
                c.execute("""INSERT INTO worker_jobs
                  (id,owner_id,kind,payload,priority,idempotency_key,state,attempts,max_attempts,
                   lease_until,lease_token,run_after,result,error_code,created_at,updated_at)
                  VALUES(?,?,?,?,?,?,'queued',0,?,NULL,NULL,?,NULL,NULL,?,?)""",
                  (job_id, owner_id, kind, json.dumps(payload, sort_keys=True), priority,
                   idempotency_key, self.max_attempts, run_after or stamp, stamp, stamp))
                self._event(c, job_id, "job.queued")
        return job_id

    def claim(self, owner_id=None):
        stamp = now()
        lease = (datetime.now(timezone.utc) + timedelta(seconds=self.lease_seconds)).isoformat(timespec="seconds")
        lease_token = secrets.token_urlsafe(24)
        with self.engine.db() as c:
            c.execute("BEGIN IMMEDIATE")
            recovery_sql = """UPDATE worker_jobs
                       SET state=CASE WHEN attempts>=max_attempts THEN 'failed' ELSE 'queued' END,
                           error_code=CASE WHEN attempts>=max_attempts THEN 'lease_expired' ELSE error_code END,
                           lease_until=NULL,lease_token=NULL,updated_at=? WHERE state='running' AND lease_until<?"""
            recovery_args = [stamp, stamp]
            if owner_id is not None:
                recovery_sql += " AND owner_id=?"
                recovery_args.append(owner_id)
            expired_sql = "SELECT id,attempts,max_attempts FROM worker_jobs WHERE state='running' AND lease_until<?"
            expired_args = [stamp]
            if owner_id is not None:
                expired_sql += " AND owner_id=?"
                expired_args.append(owner_id)
            expired = c.execute(expired_sql, expired_args).fetchall()
            for row in expired:
                terminal = row["attempts"] >= row["max_attempts"]
                self._event(c, row["id"], "job.failed" if terminal else "job.requeued",
                            {"reason": "lease_expired", "attempt": row["attempts"]})
            c.execute(recovery_sql, recovery_args)
            if owner_id is None:
                row = c.execute("SELECT * FROM worker_jobs WHERE state='queued' AND run_after<=? ORDER BY priority DESC,created_at LIMIT 1",
                                (stamp,)).fetchone()
            else:
                row = c.execute("SELECT * FROM worker_jobs WHERE state='queued' AND owner_id=? AND run_after<=? ORDER BY priority DESC,created_at LIMIT 1",
                                (owner_id, stamp)).fetchone()
            if row is None:
                return None
            attempts = row["attempts"] + 1
            c.execute("UPDATE worker_jobs SET state='running',attempts=?,lease_until=?,lease_token=?,updated_at=? WHERE id=? AND state='queued'",
                      (attempts, lease, lease_token, stamp, row["id"]))
            self._event(c, row["id"], "job.claimed", {"attempt": attempts})
            result = dict(row)
            result.update(state="running", attempts=attempts, lease_until=lease, lease_token=lease_token)
            return result

    def complete(self, job_id, result, *, lease_token):
        encoded = json.dumps(result, ensure_ascii=False)
        if len(encoded) > 32_000:
            raise ValueError("job result too large")
        with self.engine.db() as c:
            cur = c.execute("UPDATE worker_jobs SET state='completed',result=?,lease_until=NULL,lease_token=NULL,updated_at=? WHERE id=? AND state='running' AND lease_token=?",
                            (encoded, now(), job_id, lease_token))
            if cur.rowcount != 1:
                raise ValueError("job is not running")
            self._event(c, job_id, "job.completed")

    def renew(self, job_id, *, lease_token):
        """Extend a live lease only while this worker still owns its fencing token."""
        lease = (datetime.now(timezone.utc) + timedelta(seconds=self.lease_seconds)).isoformat(timespec="seconds")
        with self.engine.db() as c:
            cursor = c.execute("UPDATE worker_jobs SET lease_until=?,updated_at=? WHERE id=? AND state='running' AND lease_token=?",
                               (lease, now(), job_id, lease_token))
            return cursor.rowcount == 1

    def fail(self, job_id, error_code, *, lease_token):
        if not isinstance(error_code, str) or not error_code.replace("_", "").isalnum() or len(error_code) > 64:
            raise ValueError("invalid error code")
        with self.engine.db() as c:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute("SELECT attempts,max_attempts FROM worker_jobs WHERE id=? AND state='running' AND lease_token=?",
                             (job_id, lease_token)).fetchone()
            if row is None:
                raise ValueError("job is not running")
            state = "failed" if row["attempts"] >= row["max_attempts"] else "queued"
            delay = 0 if state == "failed" else min(300, 2 ** row["attempts"])
            due = (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat(timespec="seconds")
            c.execute("UPDATE worker_jobs SET state=?,error_code=?,lease_until=NULL,lease_token=NULL,run_after=?,updated_at=? WHERE id=?",
                      (state, error_code, due, now(), job_id))
            self._event(c, job_id, "job." + state, {"error_code": error_code})
            return state

    def cancel(self, job_id):
        with self.engine.db() as c:
            cur = c.execute("UPDATE worker_jobs SET state='cancelled',lease_until=NULL,lease_token=NULL,updated_at=? WHERE id=? AND state='queued'",
                            (now(), job_id))
            if cur.rowcount:
                self._event(c, job_id, "job.cancelled")
            return cur.rowcount == 1

    def get(self, job_id, *, owner_id=None):
        with self.engine.db() as c:
            query = "SELECT id,owner_id,kind,payload,priority,idempotency_key,state,attempts,max_attempts,lease_until,run_after,result,error_code,created_at,updated_at FROM worker_jobs WHERE id=?"
            args = [job_id]
            if owner_id is not None:
                query += " AND owner_id=?"
                args.append(owner_id)
            row = c.execute(query, args).fetchone()
            return dict(row) if row else None

    def list(self, limit=100, *, owner_id=None):
        with self.engine.db() as c:
            query = "SELECT id,owner_id,kind,payload,priority,idempotency_key,state,attempts,max_attempts,lease_until,run_after,result,error_code,created_at,updated_at FROM worker_jobs"
            args = []
            if owner_id is not None:
                query += " WHERE owner_id=?"
                args.append(owner_id)
            query += " ORDER BY created_at DESC LIMIT ?"
            args.append(max(1, min(int(limit), 500)))
            return [dict(r) for r in c.execute(query, args).fetchall()]

    def events(self, job_id, *, owner_id=None):
        with self.engine.db() as c:
            if owner_id is not None and not c.execute("SELECT 1 FROM worker_jobs WHERE id=? AND owner_id=?",
                                                       (job_id, owner_id)).fetchone():
                return []
            return [dict(r) for r in c.execute("SELECT event,details,created_at FROM worker_job_events WHERE job_id=? ORDER BY rowid",
                                                 (job_id,)).fetchall()]

    def counts(self, *, owner_id=None):
        with self.engine.db() as c:
            if owner_id is None:
                rows = c.execute("SELECT state,COUNT(*) AS count FROM worker_jobs GROUP BY state").fetchall()
            else:
                rows = c.execute("SELECT state,COUNT(*) AS count FROM worker_jobs WHERE owner_id=? GROUP BY state",
                                 (owner_id,)).fetchall()
            return {row["state"]: row["count"] for row in rows}

    def by_idempotency_key(self, key, *, owner_id=None):
        with self.engine.db() as c:
            if owner_id is None:
                row = c.execute("SELECT id,state,kind,owner_id FROM worker_jobs WHERE idempotency_key=?",
                                (key,)).fetchone()
            else:
                row = c.execute("SELECT id,state,kind,owner_id FROM worker_jobs WHERE idempotency_key=? AND owner_id=?",
                                (key, owner_id)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def _event(c, job_id, event, details=None):
        c.execute("INSERT INTO worker_job_events VALUES(?,?,?,?,?)",
                  (uid("wje"), job_id, event, json.dumps(details or {}, sort_keys=True), now()))


class LocalWorker:
    """A stoppable single-thread worker with an explicit handler allowlist."""
    def __init__(self, queue, cycles=None):
        self.queue = queue
        self.cycles = cycles
        self.worker_id = uid("worker")
        self.stop_event = threading.Event()
        self.handlers = {"memory.consolidate": lambda payload: queue.engine.consolidation_report(),
                         "learning.stats": lambda payload: queue.engine.stats()}
        if cycles is not None:
            self.handlers["learning.cycle_step"] = lambda payload: cycles.run_step(payload["cycle_id"])

    def run_once(self, owner_id=None):
        self._heartbeat("running")
        if self.cycles is not None:
            self.cycles.schedule_due(owner_id=owner_id)
            self.cycles.recover_running(owner_id=owner_id)
        job = self.queue.claim(owner_id=owner_id)
        if job is None:
            self._heartbeat("idle")
            return False
        renewal_stop = threading.Event()
        lease_lost = threading.Event()
        interval = max(0.1, self.queue.lease_seconds / 3)

        def renew_while_running():
            while not renewal_stop.wait(interval):
                try:
                    if not self.queue.renew(job["id"], lease_token=job["lease_token"]):
                        lease_lost.set()
                        return
                    try:
                        self._heartbeat("running")
                    except Exception:
                        # Monitoring failure must not revoke an otherwise valid lease.
                        pass
                except Exception:
                    # Without a confirmed renewal, do not claim the result was committed.
                    lease_lost.set()
                    return

        renewal = threading.Thread(target=renew_while_running,
                                   name=f"lease-renew-{job['id']}", daemon=True)
        renewal.start()
        try:
            result = self.handlers[job["kind"]](json.loads(job["payload"]))
        except Exception:
            renewal_stop.set()
            renewal.join(timeout=max(1.0, interval * 2))
            if not lease_lost.is_set():
                self._fail_job(job)
            self._heartbeat("idle")
            return True
        finally:
            renewal_stop.set()
            renewal.join(timeout=max(1.0, interval * 2))
        if lease_lost.is_set() or not self.queue.renew(job["id"], lease_token=job["lease_token"]):
            self._heartbeat("idle")
            return True
        try:
            self.queue.complete(job["id"], result, lease_token=job["lease_token"])
        except Exception as exc:
            if not (isinstance(exc, ValueError) and str(exc) == "job is not running"):
                self._fail_job(job)
            self._heartbeat("idle")
            return True
        self._heartbeat("idle")
        return True

    def _fail_job(self, job):
        try:
            state = self.queue.fail(job["id"], "worker_execution_failed", lease_token=job["lease_token"])
        except ValueError:
            # A reclaimed lease fences this worker from changing retry state.
            return None
        if state == "failed" and self.cycles is not None and job["kind"] == "learning.cycle_step":
            try:
                self.cycles._set_status(json.loads(job["payload"])["cycle_id"],
                                        "paused_error", "worker_retries_exhausted")
            except Exception:
                pass
        return state

    def _heartbeat(self, state):
        stamp = now()
        with self.queue.engine.db() as c:
            c.execute("""INSERT INTO worker_instances VALUES(?,?,?,?)
                         ON CONFLICT(id) DO UPDATE SET state=excluded.state,heartbeat_at=excluded.heartbeat_at""",
                      (self.worker_id, state, stamp, stamp))

    def status(self):
        with self.queue.engine.db() as c:
            row = c.execute("SELECT state,started_at,heartbeat_at FROM worker_instances ORDER BY heartbeat_at DESC LIMIT 1").fetchone()
            return dict(row) if row else {"state": "not_seen", "started_at": None, "heartbeat_at": None}

    def run_forever(self, poll_seconds=1):
        try:
            while not self.stop_event.is_set():
                if not self.run_once():
                    self.stop_event.wait(poll_seconds)
        finally:
            self._heartbeat("stopped")

    def stop(self):
        self.stop_event.set()
