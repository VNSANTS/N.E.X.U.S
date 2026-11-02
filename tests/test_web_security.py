import unittest
from pathlib import Path


class WebSecurityTests(unittest.TestCase):
    def test_api_token_is_not_persisted_in_browser_storage(self):
        source = (Path(__file__).parents[1] / "nexus_learning" / "web" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("sessionStorage", source)
        self.assertNotIn("nexus_token", source)
        self.assertIn("token=d.access_token", source)

    def test_streaming_auth_expiry_returns_user_to_login(self):
        source = (Path(__file__).parents[1] / "nexus_learning" / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn("response.status===401", source)
        self.assertIn("Sessão expirada. Entre novamente.", source)


if __name__ == "__main__":
    unittest.main()
