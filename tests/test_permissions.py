import tempfile
import unittest

from nexus_learning.engine import LearningEngine
from nexus_learning.permissions import PermissionManager


class PermissionManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = LearningEngine(self.tmp.name + "/test.db")
        self.permissions = PermissionManager(self.engine)

    def tearDown(self):
        self.tmp.cleanup()

    def test_standard_access_can_be_granted_and_revoked(self):
        status = self.permissions.grant_standard_access()
        self.assertIn("memory.read", status["granted"])
        self.assertTrue(self.permissions.authorize("memory.read"))
        self.permissions.revoke("memory.read")
        self.assertFalse(self.permissions.authorize("memory.read"))

    def test_high_impact_scope_requires_fresh_confirmation(self):
        with self.assertRaises(PermissionError):
            self.permissions.grant("external.send")
        self.assertFalse(self.permissions.authorize("external.send"))
        self.assertTrue(self.permissions.authorize("external.send", confirmed=True))

    def test_unknown_scope_is_rejected(self):
        with self.assertRaises(ValueError):
            self.permissions.grant("root.access")

    def test_audit_log_records_decisions(self):
        self.permissions.grant_standard_access()
        self.permissions.authorize("memory.read")
        self.assertGreaterEqual(len(self.permissions.audit_log()), 2)


if __name__ == "__main__":
    unittest.main()
