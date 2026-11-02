import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TermuxLauncherTests(unittest.TestCase):
    def test_termux_launchers_have_valid_posix_shell_syntax(self):
        for relative in ("scripts/termux-start.sh", "scripts/termux-worker.sh"):
            with self.subTest(script=relative):
                completed = subprocess.run(
                    ["sh", "-n", str(ROOT / relative)],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_api_and_worker_share_private_database_and_api_stays_loopback_only(self):
        api = (ROOT / "scripts/termux-start.sh").read_text(encoding="utf-8")
        worker = (ROOT / "scripts/termux-worker.sh").read_text(encoding="utf-8")
        database_default = '"$HOME/nexus-data/nexus_learning.db"'
        self.assertIn(database_default, api)
        self.assertIn(database_default, worker)
        self.assertIn('--host 127.0.0.1 --port 8765', api)
        self.assertNotIn('--host 0.0.0.0', api)
        self.assertNotIn('0.0.0.0', api)


if __name__ == "__main__":
    unittest.main()
