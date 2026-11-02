import json
from concurrent.futures import ThreadPoolExecutor
import threading
from contextlib import contextmanager
from pathlib import Path
import tempfile
import unittest

from nexus_learning.engine import LearningEngine
from nexus_learning.learning_cycles import LearningCycleService
from nexus_learning.research import ResearchService
from nexus_learning.worker import LocalWorker, TaskQueue


class FakeDiscovery:
    name = "fake_discovery"

    def __init__(self):
        self.calls = []

    def search(self, query, limit=5):
        self.calls.append((query, limit))
        return []


class CycleRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = str(Path(self.temp.name) / "recovery.db")
        self.discovery = FakeDiscovery()
        self._open_services()
        self.owner = "owner-recovery"

    def tearDown(self):
        self.engine.close()
        self.temp.cleanup()

    def _open_services(self):
        self.engine = LearningEngine(self.database)
        self.queue = TaskQueue(self.engine, max_attempts=3, lease_seconds=30)
        self.research = ResearchService(self.engine, self.discovery, min_interval_seconds=0)
        self.cycles = LearningCycleService(self.engine, self.queue, research_enabled=True,
                                           research_service=self.research)

    def _restart_services(self):
        self.engine.close()
        self._open_services()

    def _run_one(self):
        return LocalWorker(self.queue, cycles=self.cycles).run_once(owner_id=self.owner)

    def test_existing_research_reservation_schema_is_migrated(self):
        legacy = LearningEngine(":memory:")
        try:
            with legacy.db() as connection:
                connection.execute("""CREATE TABLE learning_research_reservations(
                    cycle_id TEXT PRIMARY KEY,status TEXT NOT NULL,providers_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,updated_at TEXT NOT NULL)""")
            queue = TaskQueue(legacy)
            LearningCycleService(legacy, queue)
            with legacy.db() as connection:
                columns = {row["name"] for row in connection.execute(
                    "PRAGMA table_info(learning_research_reservations)").fetchall()}
            self.assertIn("result_json", columns)
        finally:
            legacy.close()

    def test_provider_failure_identifiers_are_allowlisted_before_persistence(self):
        safe = self.cycles._safe_provider_failures([{
            "provider": "secretkey123456789", "operation": "search?token=secret",
            "error_type": "secretkey987654321", "message": "must not survive",
        }])
        self.assertEqual(safe, [{"provider": "custom", "operation": "other",
                                 "error_type": "ExternalError"}])

    def _advance_to(self, topic, phase):
        cycle = self.cycles.start_cycle(topic["id"], self.owner)
        while self.cycles.get_cycle(cycle["id"], self.owner)["phase"] != phase:
            self.assertTrue(self._run_one())
        return cycle

    def test_expired_claim_is_recovered_after_engine_reconstruction(self):
        topic = self.cycles.create_topic(self.owner, "routine recovery")
        cycle = self.cycles.start_cycle(topic["id"], self.owner)
        claimed = self.queue.claim(owner_id=self.owner)
        self.assertEqual(json.loads(claimed["payload"])["cycle_id"], cycle["id"])
        with self.engine.db() as connection:
            connection.execute("UPDATE worker_jobs SET lease_until='2000-01-01T00:00:00+00:00' WHERE id=?",
                               (claimed["id"],))

        self._restart_services()
        self.assertTrue(self._run_one())
        resumed = self.cycles.get_cycle(cycle["id"], self.owner)
        self.assertEqual((resumed["phase"], resumed["steps_used"]), ("opportunity", 1))

    def test_cycle_phase_resumes_from_last_checkpoint_if_next_enqueue_was_lost(self):
        topic = self.cycles.create_topic(self.owner, "enqueue recovery")
        cycle = self.cycles.start_cycle(topic["id"], self.owner)
        claimed = self.queue.claim(owner_id=self.owner)
        original_enqueue = self.cycles._enqueue_step

        def crash_after_checkpoint(cycle_id):
            raise RuntimeError("simulated process stop after phase commit")

        self.cycles._enqueue_step = crash_after_checkpoint
        try:
            with self.assertRaisesRegex(RuntimeError, "after phase commit"):
                self.cycles.run_step(cycle["id"])
        finally:
            self.cycles._enqueue_step = original_enqueue
        self.queue.fail(claimed["id"], "simulated_worker_exit", lease_token=claimed["lease_token"])
        checkpointed = self.cycles.get_cycle(cycle["id"], self.owner)
        self.assertEqual((checkpointed["phase"], checkpointed["steps_used"]), ("opportunity", 1))

        self._restart_services()
        self.assertTrue(self._run_one())
        resumed = self.cycles.get_cycle(cycle["id"], self.owner)
        self.assertEqual((resumed["phase"], resumed["steps_used"]), ("plan", 2))

    def test_opportunity_retry_does_not_duplicate_pending_question(self):
        topic = self.cycles.create_topic(self.owner, "qual decisão devo tomar para mim")
        cycle = self._advance_to(topic, "opportunity")
        original_run_phase = self.cycles._run_phase
        crashed = False

        def run_then_crash(snapshot, topic_row, settings):
            nonlocal crashed
            result = original_run_phase(snapshot, topic_row, settings)
            if snapshot["phase"] == "opportunity" and not crashed:
                crashed = True
                raise RuntimeError("simulated interruption after question write")
            return result

        self.cycles._run_phase = run_then_crash
        try:
            self.assertTrue(self._run_one())
        finally:
            self.cycles._run_phase = original_run_phase
        with self.engine.db() as connection:
            connection.execute("UPDATE worker_jobs SET run_after='2000-01-01T00:00:00+00:00' WHERE state='queued'")

        self._restart_services()
        self.assertTrue(self._run_one())
        questions = self.cycles.questions(self.owner, "pending")
        self.assertEqual(len([q for q in questions if q["cycle_id"] == cycle["id"]]), 1)

    def test_interrupted_research_reservation_is_not_sent_again(self):
        self.cycles.update_settings(enabled=True, level="metadata_research", max_cycles_per_day=5,
                                    max_sources_per_cycle=3, max_research_calls_per_day=4)
        topic = self.cycles.create_topic(self.owner, "local recovery research", allow_research=True)
        cycle = self._advance_to(topic, "research")
        original_reserve = self.cycles._reserve_research_call

        def reserve_then_crash(snapshot, topic_row, settings):
            allowed = original_reserve(snapshot, topic_row, settings)
            if allowed[0]:
                raise RuntimeError("simulated interruption after research reservation")
            return allowed

        self.cycles._reserve_research_call = reserve_then_crash
        try:
            self.assertTrue(self._run_one())
        finally:
            self.cycles._reserve_research_call = original_reserve
        with self.engine.db() as connection:
            connection.execute("UPDATE worker_jobs SET run_after='2000-01-01T00:00:00+00:00' WHERE state='queued'")

        self._restart_services()
        self.assertTrue(self._run_one())
        self.assertEqual(self.discovery.calls, [])
        resumed = self.cycles.get_cycle(cycle["id"], self.owner)
        self.assertEqual(resumed["checkpoint"]["research"]["status"], "interrupted_uncertain")

    def test_overlapping_workers_only_reserve_one_research_call_per_cycle(self):
        self.cycles.update_settings(enabled=True, level="metadata_research", max_cycles_per_day=5,
                                    max_sources_per_cycle=3, max_research_calls_per_day=4)
        topic = self.cycles.create_topic(self.owner, "concurrent research reservation", allow_research=True)
        cycle = self._advance_to(topic, "research")
        snapshot = self.cycles.get_cycle(cycle["id"], self.owner)
        settings = self.cycles.settings()
        barrier = threading.Barrier(2)

        def reserve_once():
            barrier.wait(timeout=2)
            return self.cycles._reserve_research_call(snapshot, topic, settings)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: reserve_once(), range(2)))
        self.assertEqual(sum(1 for allowed, _ in results if allowed), 1)
        with self.engine.db() as connection:
            reservations = connection.execute("SELECT COUNT(*) FROM learning_cycle_events WHERE cycle_id=? AND event='research.requested'",
                                              (cycle["id"],)).fetchone()[0]
        self.assertEqual(reservations, 1)

    def test_completed_research_result_survives_crash_before_cycle_checkpoint(self):
        self.cycles.update_settings(enabled=True, level="metadata_research", max_cycles_per_day=5,
                                    max_sources_per_cycle=3, max_research_calls_per_day=4)
        topic = self.cycles.create_topic(self.owner, "completed research recovery", allow_research=True)
        cycle = self._advance_to(topic, "research")
        original_complete = self.cycles._complete_research_reservation
        crashed = False

        def complete_then_crash(cycle_id, outcome):
            nonlocal crashed
            original_complete(cycle_id, outcome)
            if not crashed:
                crashed = True
                raise RuntimeError("simulated interruption after research completion")

        self.cycles._complete_research_reservation = complete_then_crash
        try:
            self.assertTrue(self._run_one())
        finally:
            self.cycles._complete_research_reservation = original_complete
        with self.engine.db() as connection:
            connection.execute("UPDATE worker_jobs SET run_after='2000-01-01T00:00:00+00:00' WHERE state='queued'")

        self._restart_services()
        self.assertTrue(self._run_one())
        resumed = self.cycles.get_cycle(cycle["id"], self.owner)
        self.assertEqual(resumed["checkpoint"]["research"]["status"], "no_results")
        self.assertFalse(resumed["checkpoint"]["research"]["network_used"] is False)
        self.assertEqual(len(self.discovery.calls), 1)

    def test_partial_research_failure_outcome_survives_checkpoint_interruption(self):
        self.cycles.update_settings(enabled=True, level="metadata_research", max_cycles_per_day=5,
                                    max_sources_per_cycle=3, max_research_calls_per_day=4)
        topic = self.cycles.create_topic(self.owner, "partial research recovery", allow_research=True)
        cycle = self._advance_to(topic, "research")
        self.discovery.last_failures = [{"provider": "fake_discovery", "operation": "search",
                                         "error_type": "TimeoutError", "message": "secret-like detail"}]
        original_complete = self.cycles._complete_research_reservation
        crashed = False

        def complete_then_crash(cycle_id, outcome):
            nonlocal crashed
            original_complete(cycle_id, outcome)
            if not crashed:
                crashed = True
                raise RuntimeError("simulated interruption after partial outcome persistence")

        self.cycles._complete_research_reservation = complete_then_crash
        try:
            self.assertTrue(self._run_one())
        finally:
            self.cycles._complete_research_reservation = original_complete
        with self.engine.db() as connection:
            connection.execute("UPDATE worker_jobs SET run_after='2000-01-01T00:00:00+00:00' WHERE state='queued'")

        self._restart_services()
        self.assertTrue(self._run_one())
        resumed = self.cycles.get_cycle(cycle["id"], self.owner)
        outcome = resumed["checkpoint"]["research"]
        self.assertEqual(outcome["status"], "failed")
        self.assertEqual(outcome["provider_failures"], [{"provider": "fake_discovery", "operation": "search",
                                                          "error_type": "TimeoutError"}])
        self.assertNotIn("message", json.dumps(outcome))
        self.assertEqual(len(self.discovery.calls), 1)

    def test_gap_task_and_link_commit_atomically_across_retry(self):
        topic = self.cycles.create_topic(self.owner, "gap task recovery")
        cycle = self.cycles.start_cycle(topic["id"], self.owner)
        with self.engine.db() as connection:
            connection.execute("UPDATE learning_cycles SET phase='gaps',steps_used=9 WHERE id=?",
                               (cycle["id"],))
        self.cycles._finding(cycle["id"], "next_study", "Recover a task once", {"topic": topic["topic"]})
        finding = next(x for x in self.cycles.findings(cycle_id=cycle["id"])
                       if x["title"] == "Recover a task once")
        finding_id = finding["id"]
        original_findings = self.cycles.findings
        self.cycles.findings = lambda **kwargs: [finding]
        original_db = self.engine.db
        fail_once = True

        @contextmanager
        def interrupt_before_link():
            nonlocal fail_once
            with original_db() as connection:
                class ConnectionProxy:
                    def execute(self, sql, *args):
                        nonlocal fail_once
                        if fail_once and sql.lstrip().upper().startswith(
                                "INSERT OR IGNORE INTO LEARNING_CYCLE_TASK_LINKS"):
                            fail_once = False
                            raise RuntimeError("simulated interruption before task link")
                        return connection.execute(sql, *args)

                    def __getattr__(self, name):
                        return getattr(connection, name)

                yield ConnectionProxy()

        self.engine.db = interrupt_before_link
        try:
            with self.assertRaisesRegex(RuntimeError, "before task link"):
                self.cycles._run_phase(
                    {**cycle, "phase": "gaps", "steps_used": 9,
                     "checkpoint": cycle["checkpoint"]},
                    {**topic, "next_run": topic["next_run"]}, self.cycles.settings())
        finally:
            self.engine.db = original_db
            self.cycles.findings = original_findings

        self.cycles._run_phase(
            {**cycle, "phase": "gaps", "steps_used": 9,
             "checkpoint": cycle["checkpoint"]},
            {**topic, "next_run": topic["next_run"]}, self.cycles.settings())
        with self.engine.db() as connection:
            task_count = connection.execute("SELECT COUNT(*) FROM tasks WHERE title=?",
                                            ("Revisar aprendizagem: Recover a task once",)).fetchone()[0]
            link_count = connection.execute("SELECT COUNT(*) FROM learning_cycle_task_links WHERE cycle_id=? AND finding_id=?",
                                            (cycle["id"], finding_id)).fetchone()[0]
        self.assertEqual((task_count, link_count), (1, 1))


if __name__ == "__main__":
    unittest.main()
