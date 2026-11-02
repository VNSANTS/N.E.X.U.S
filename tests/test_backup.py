import sqlite3
import tempfile
import unittest
from pathlib import Path

from nexus_learning.backup import backup_database, restore_database


class DatabaseBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source.db"
        with sqlite3.connect(self.source) as connection:
            connection.execute("CREATE TABLE records(value TEXT NOT NULL)")
            connection.execute("INSERT INTO records VALUES('original')")
        self.backup = self.root / "backup.db"
        self.target = self.root / "target.db"

    def tearDown(self):
        self.temp.cleanup()

    def values(self, path):
        with sqlite3.connect(path) as connection:
            return [row[0] for row in connection.execute("SELECT value FROM records")]

    def test_backup_is_consistent_and_preserves_data(self):
        result = backup_database(self.source, self.backup)
        self.assertEqual(result, self.backup.resolve())
        self.assertEqual(self.values(self.backup), ["original"])
        with sqlite3.connect(self.backup) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_backup_refuses_overwrite_by_default(self):
        backup_database(self.source, self.backup)
        with self.assertRaises(FileExistsError):
            backup_database(self.source, self.backup)
        self.assertEqual(self.values(self.backup), ["original"])

    def test_backup_overwrite_requires_explicit_flag(self):
        backup_database(self.source, self.backup)
        with sqlite3.connect(self.source) as connection:
            connection.execute("INSERT INTO records VALUES('new')")
        backup_database(self.source, self.backup, overwrite=True)
        self.assertEqual(self.values(self.backup), ["original", "new"])

    def test_restore_creates_database_when_destination_is_absent(self):
        backup_database(self.source, self.backup)
        restore_database(self.backup, self.target)
        self.assertEqual(self.values(self.target), ["original"])

    def test_restore_refuses_overwrite_without_explicit_flag(self):
        backup_database(self.source, self.backup)
        with sqlite3.connect(self.target) as connection:
            connection.execute("CREATE TABLE records(value TEXT NOT NULL)")
            connection.execute("INSERT INTO records VALUES('keep')")
        with self.assertRaises(FileExistsError):
            restore_database(self.backup, self.target)
        self.assertEqual(self.values(self.target), ["keep"])

    def test_restore_overwrite_requires_and_creates_safety_backup(self):
        backup_database(self.source, self.backup)
        with sqlite3.connect(self.target) as connection:
            connection.execute("CREATE TABLE records(value TEXT NOT NULL)")
            connection.execute("INSERT INTO records VALUES('before')")
        with self.assertRaises(ValueError):
            restore_database(self.backup, self.target, overwrite=True)
        safety = self.root / "before-restore.db"
        restore_database(self.backup, self.target, overwrite=True, safety_backup=safety)
        self.assertEqual(self.values(self.target), ["original"])
        self.assertEqual(self.values(safety), ["before"])

    def test_restore_rejects_invalid_backup_without_touching_target(self):
        self.backup.write_bytes(b"not a sqlite database")
        with sqlite3.connect(self.target) as connection:
            connection.execute("CREATE TABLE records(value TEXT NOT NULL)")
            connection.execute("INSERT INTO records VALUES('keep')")
        with self.assertRaises(sqlite3.DatabaseError):
            restore_database(self.backup, self.target, overwrite=True,
                             safety_backup=self.root / "safety.db")
        self.assertEqual(self.values(self.target), ["keep"])
        self.assertFalse((self.root / "safety.db").exists())

    def test_same_file_and_missing_source_are_rejected(self):
        with self.assertRaises(ValueError):
            backup_database(self.source, self.source)
        with self.assertRaises(FileNotFoundError):
            backup_database(self.root / "missing.db", self.backup)

    def test_symbolic_link_database_paths_are_rejected(self):
        link = self.root / "source-link.db"
        link.symlink_to(self.source)
        with self.assertRaises(ValueError):
            backup_database(link, self.backup)

    def test_safety_backup_must_be_a_distinct_new_file(self):
        backup_database(self.source, self.backup)
        with sqlite3.connect(self.target) as connection:
            connection.execute("CREATE TABLE records(value TEXT NOT NULL)")
        with self.assertRaises(ValueError):
            restore_database(self.backup, self.target, overwrite=True,
                             safety_backup=self.backup)
        self.assertTrue(self.target.exists())


if __name__ == "__main__":
    unittest.main()
