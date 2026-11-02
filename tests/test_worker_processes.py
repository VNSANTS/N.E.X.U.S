"""Process-level checks for SQLite job claims, idempotency and lease fencing."""
import multiprocessing
from pathlib import Path
import tempfile
import unittest

from nexus_learning.engine import LearningEngine
from nexus_learning.worker import TaskQueue


def _process_queue_operation(database, barrier, output, operation):
    engine = LearningEngine(database)
    try:
        queue = TaskQueue(engine, max_attempts=3, lease_seconds=30)
        barrier.wait(timeout=15)
        if operation == "claim":
            claimed = queue.claim()
            output.put({"id": claimed["id"] if claimed else None,
                        "token": claimed["lease_token"] if claimed else None})
        elif operation == "enqueue":
            output.put({"id": queue.enqueue("learning.stats", owner_id="owner",
                                               idempotency_key="shared-process-key")})
    except BaseException as exc:
        output.put({"error": type(exc).__name__})
    finally:
        engine.close()


class WorkerProcessTests(unittest.TestCase):
    def _run_two_processes(self, database, operation):
        context = multiprocessing.get_context("spawn")
        barrier = context.Barrier(2)
        output = context.Queue()
        processes = [context.Process(target=_process_queue_operation,
                                     args=(database, barrier, output, operation))
                     for _ in range(2)]
        try:
            for process in processes:
                process.start()
            results = [output.get(timeout=30) for _ in processes]
            for process in processes:
                process.join(timeout=10)
                self.assertFalse(process.is_alive(), "worker subprocess did not exit")
                self.assertEqual(process.exitcode, 0)
            self.assertFalse(any("error" in result for result in results), results)
            return results
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)
            output.close()

    def test_independent_processes_cannot_claim_the_same_job(self):
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "worker-processes.db")
            engine = LearningEngine(database)
            queue = TaskQueue(engine, lease_seconds=30)
            expected = queue.enqueue("learning.stats", owner_id="owner")
            engine.close()

            claims = self._run_two_processes(database, "claim")

            self.assertEqual(sum(claim["id"] == expected for claim in claims), 1)
            self.assertEqual(sum(claim["id"] is None for claim in claims), 1)

    def test_independent_processes_share_one_idempotent_enqueue(self):
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "worker-enqueue-processes.db")
            engine = LearningEngine(database)
            TaskQueue(engine)
            engine.close()

            results = self._run_two_processes(database, "enqueue")

            self.assertEqual(results[0]["id"], results[1]["id"])
            engine = LearningEngine(database)
            try:
                with engine.db() as connection:
                    self.assertEqual(connection.execute(
                        "SELECT COUNT(*) FROM worker_jobs WHERE idempotency_key=?",
                        ("shared-process-key",)).fetchone()[0], 1)
            finally:
                engine.close()

    def test_reclaimed_job_rejects_previous_process_lease_token(self):
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "worker-fencing-processes.db")
            engine = LearningEngine(database)
            queue = TaskQueue(engine, lease_seconds=30)
            job_id = queue.enqueue("learning.stats", owner_id="owner")
            stale = queue.claim()
            with engine.db() as connection:
                connection.execute("UPDATE worker_jobs SET lease_until='2000-01-01T00:00:00+00:00' WHERE id=?",
                                   (job_id,))
            engine.close()

            reclaimed = self._run_two_processes(database, "claim")
            new_claim = next(result for result in reclaimed if result["id"] == job_id)
            self.assertNotEqual(stale["lease_token"], new_claim["token"])

            engine = LearningEngine(database)
            try:
                queue = TaskQueue(engine, lease_seconds=30)
                self.assertFalse(queue.renew(job_id, lease_token=stale["lease_token"]))
                with self.assertRaisesRegex(ValueError, "job is not running"):
                    queue.complete(job_id, {"stale": True}, lease_token=stale["lease_token"])
                queue.complete(job_id, {"fresh": True}, lease_token=new_claim["token"])
                self.assertEqual(queue.get(job_id)["state"], "completed")
            finally:
                engine.close()


if __name__ == "__main__":
    unittest.main()
