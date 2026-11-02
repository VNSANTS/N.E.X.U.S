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


if __name__ == "__main__":
    unittest.main()
