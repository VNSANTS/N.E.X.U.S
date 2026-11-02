from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import threading
import tempfile
import time
import unittest

from nexus_learning.engine import LearningEngine
from nexus_learning.worker import LocalWorker, TaskQueue


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.engine = LearningEngine(":memory:")
        self.queue = TaskQueue(self.engine, max_attempts=2, lease_seconds=1)

    def tearDown(self):
        self.engine.close()

    def test_idempotency_priority_allowlist_and_execution(self):
        first = self.queue.enqueue("learning.stats", idempotency_key="same-request")
        duplicate = self.queue.enqueue("learning.stats", idempotency_key="same-request")
        lower = self.queue.enqueue("memory.consolidate", priority=-1)
        self.assertEqual(first, duplicate)
        with self.assertRaises(ValueError):
            self.queue.enqueue("shell.exec", {"command": "not permitted"})
        job = self.queue.claim()
        self.assertEqual(job["id"], first)
        self.queue.complete(first, {"memories": 0}, lease_token=job["lease_token"])
        worker = LocalWorker(self.queue)
        self.assertTrue(worker.run_once())
        self.assertEqual(self.queue.get(lower)["state"], "completed")

    def test_retry_is_bounded_cancel_and_lease_recovery(self):
        job_id = self.queue.enqueue("learning.stats")
        claimed = self.queue.claim()
        self.queue.fail(job_id, "temporary_failure", lease_token=claimed["lease_token"])
        self.assertEqual(self.queue.get(job_id)["state"], "queued")
        # Make due immediately for deterministic retry testing.
        with self.engine.db() as c:
            c.execute("UPDATE worker_jobs SET run_after='2000-01-01T00:00:00+00:00' WHERE id=?", (job_id,))
        claimed = self.queue.claim()
        self.queue.fail(job_id, "temporary_failure", lease_token=claimed["lease_token"])
        self.assertEqual(self.queue.get(job_id)["state"], "failed")
        queued = self.queue.enqueue("learning.stats")
        self.assertTrue(self.queue.cancel(queued))
        self.assertEqual(self.queue.get(queued)["state"], "cancelled")

    def test_expired_lease_recovers_and_fences_stale_worker(self):
        job_id = self.queue.enqueue("learning.stats")
        stale = self.queue.claim()
        with self.engine.db() as c:
            c.execute("UPDATE worker_jobs SET lease_until='2000-01-01T00:00:00+00:00' WHERE id=?", (job_id,))
        current = self.queue.claim()
        self.assertEqual(current["id"], job_id)
        self.assertNotEqual(stale["lease_token"], current["lease_token"])
        with self.assertRaises(ValueError):
            self.queue.complete(job_id, {}, lease_token=stale["lease_token"])
        self.queue.complete(job_id, {"ok": True}, lease_token=current["lease_token"])
        self.assertEqual(self.queue.get(job_id)["state"], "completed")

    def test_stale_worker_cannot_fail_a_reclaimed_job(self):
        job_id = self.queue.enqueue("learning.stats")
        stale = self.queue.claim()
        with self.engine.db() as c:
            c.execute("UPDATE worker_jobs SET lease_until='2000-01-01T00:00:00+00:00' WHERE id=?", (job_id,))
        current = self.queue.claim()
        with self.assertRaises(ValueError):
            self.queue.fail(job_id, "old_worker_failure", lease_token=stale["lease_token"])
        self.assertEqual(self.queue.get(job_id)["state"], "running")
        self.queue.complete(job_id, {}, lease_token=current["lease_token"])

    def test_jobs_are_scoped_to_authenticated_owner(self):
        one = self.queue.enqueue("learning.stats", owner_id="user-1")
        two = self.queue.enqueue("learning.stats", owner_id="user-2")
        self.assertEqual([row["id"] for row in self.queue.list(owner_id="user-1")], [one])
        self.assertIsNone(self.queue.get(two, owner_id="user-1"))

    def test_concurrent_idempotent_enqueue_returns_one_job_for_owned_and_unowned_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = LearningEngine(f"{directory}/worker.db")
            queue = TaskQueue(engine, max_attempts=2, lease_seconds=1)
            original_db = engine.db

            @contextmanager
            def delayed_db():
                with original_db() as connection:
                    class DelayedConnection:
                        def execute(self, sql, *args):
                            cursor = connection.execute(sql, *args)
                            if sql.lstrip().upper().startswith("SELECT ID FROM WORKER_JOBS"):
                                time.sleep(0.05)
                            return cursor

                        def __getattr__(self, name):
                            return getattr(connection, name)

                    yield DelayedConnection()

            engine.db = delayed_db
            try:
                for owner_id in ("user-1", None):
                    barrier = threading.Barrier(2)

                    def enqueue():
                        barrier.wait(timeout=2)
                        try:
                            return queue.enqueue("learning.stats", owner_id=owner_id,
                                                 idempotency_key=f"parallel-{owner_id}")
                        except Exception as exc:
                            return exc

                    with ThreadPoolExecutor(max_workers=2) as pool:
                        results = list(pool.map(lambda _: enqueue(), range(2)))
                    self.assertFalse(any(isinstance(result, Exception) for result in results), results)
                    self.assertEqual(results[0], results[1])
            finally:
                engine.db = original_db
                engine.close()

    def test_long_running_handler_renews_lease_before_another_worker_can_reclaim(self):
        job_id = self.queue.enqueue("learning.stats", owner_id="owner")
        started = threading.Event()
        calls = []
        first = LocalWorker(self.queue)
        second = LocalWorker(self.queue)

        def slow_handler(payload):
            calls.append(payload)
            started.set()
            time.sleep(3.5)
            return {"finished": True}

        first.handlers["learning.stats"] = slow_handler
        second.handlers["learning.stats"] = lambda payload: calls.append(payload) or {"duplicate": True}
        first_result, errors = [], []

        def run_first():
            try:
                first_result.append(first.run_once(owner_id="owner"))
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=run_first)
        thread.start()
        self.assertTrue(started.wait(timeout=3))
        initial_heartbeat = first.status()["heartbeat_at"]
        time.sleep(2.2)
        self.assertNotEqual(first.status()["heartbeat_at"], initial_heartbeat)
        second_result = second.run_once(owner_id="owner")
        thread.join(timeout=5)

        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertFalse(second_result)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.queue.get(job_id)["state"], "completed")

    def test_invalid_oversized_result_is_retried_instead_of_left_running(self):
        job_id = self.queue.enqueue("learning.stats")
        worker = LocalWorker(self.queue)
        worker.handlers["learning.stats"] = lambda payload: {"text": "x" * 33_000}

        self.assertTrue(worker.run_once())
        self.assertEqual(self.queue.get(job_id)["state"], "queued")
        self.assertEqual(self.queue.get(job_id)["error_code"], "worker_execution_failed")

    def test_expired_final_lease_records_failure_event(self):
        queue = TaskQueue(self.engine, max_attempts=1, lease_seconds=1)
        job_id = queue.enqueue("learning.stats")
        queue.claim()
        with self.engine.db() as connection:
            connection.execute("UPDATE worker_jobs SET lease_until='2000-01-01T00:00:00+00:00' WHERE id=?",
                               (job_id,))

        self.assertIsNone(queue.claim())
        self.assertEqual(queue.get(job_id)["state"], "failed")
        self.assertEqual(queue.get(job_id)["error_code"], "lease_expired")
        self.assertEqual(queue.events(job_id)[-1]["event"], "job.failed")


if __name__ == "__main__":
    unittest.main()
