import tempfile
import unittest
from pathlib import Path

from nexus_learning.checkpoint_store import (
    CheckpointConflict, CheckpointError, CheckpointNotFound, CheckpointStore,
)
from nexus_learning.engine import LearningEngine


class CheckpointStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = LearningEngine(str(Path(self.tmp.name) / "state.db"))
        self.store = CheckpointStore(self.engine)
        self.store.create("task-1", "owner-a", "session-a", "a" * 64, "mock:model")

    def tearDown(self):
        self.engine.close()
        self.tmp.cleanup()

    def lease(self):
        return self.store.acquire("task-1", "owner-a", "session-a")["lease_token"]

    def test_owner_and_session_are_required(self):
        self.assertIsNone(self.store.get("task-1", "owner-b"))
        with self.assertRaises(CheckpointNotFound):
            self.store.acquire("task-1", "owner-b", "session-a")
        with self.assertRaises(CheckpointNotFound):
            self.store.acquire("task-1", "owner-a", "other-session")

    def test_stage_order_and_typed_result(self):
        token = self.lease()
        with self.assertRaises(CheckpointConflict):
            self.store.start_stage("task-1", "owner-a", token, "analyst", "mock", "m", "b" * 64)
        self.store.start_stage("task-1", "owner-a", token, "architect", "mock", "m", "b" * 64)
        self.store.complete_stage("task-1", "owner-a", token, "architect",
                                  {"summary": "plan", "items": ["step"], "claims": [], "reviews": []})
        state = self.store.get("task-1", "owner-a")
        self.assertEqual(state["stages"][0]["state"], "completed")
        self.assertEqual(state["stages"][0]["deliverable_json"],
                         '{"claims":[],"items":["step"],"reviews":[],"summary":"plan"}')

    def test_unknown_fields_and_oversized_values_are_rejected(self):
        with self.assertRaises(CheckpointError):
            self.store._json({"summary": "ok", "prompt": "must not persist"})
        with self.assertRaises(CheckpointError):
            self.store._json({"summary": "x" * 161})

    def test_expired_or_stale_lease_cannot_write(self):
        token = self.lease()
        self.store.start_stage("task-1", "owner-a", token, "architect", "mock", "m", "c" * 64)
        with self.assertRaises(CheckpointConflict):
            self.store.acquire("task-1", "owner-a", "session-a")

    def test_ambiguous_stage_needs_explicit_retry_confirmation(self):
        token = self.lease()
        self.store.start_stage("task-1", "owner-a", token, "architect", "mock", "m", "d" * 64)
        self.store.fail_stage("task-1", "owner-a", token, "architect", ambiguous=True)
        self.store.release("task-1", "owner-a", token)
        token2 = self.lease()
        with self.assertRaises(CheckpointConflict):
            self.store.authorize_stage_retry("task-1", "owner-a", token2, "architect")
        self.store.authorize_stage_retry("task-1", "owner-a", token2, "architect",
                                         confirm_ambiguous=True)
        state = self.store.get("task-1", "owner-a")
        self.assertEqual(state["attempt"], 2)
        self.assertEqual(state["stages"][0]["state"], "pending")

    def test_running_stage_becomes_unknown_after_resume_claim(self):
        token = self.lease()
        self.store.start_stage("task-1", "owner-a", token, "architect", "mock", "m", "e" * 64)
        self.store.release("task-1", "owner-a", token)
        token2 = self.lease()
        self.assertEqual(self.store.get("task-1", "owner-a")["stages"][0]["state"],
                         "interrupted_unknown")
        with self.assertRaises(CheckpointConflict):
            self.store.start_stage("task-1", "owner-a", token2, "architect", "mock", "m", "e" * 64)


if __name__ == "__main__":
    unittest.main()
