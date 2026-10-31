import io
import json
import unittest
from unittest.mock import patch

from nexus_learning.crossref import CrossrefClient, CrossrefError


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class CrossrefClientTests(unittest.TestCase):
    def test_search_normalizes_metadata_and_uses_polite_pool(self):
        payload = {"message": {"items": [{
            "title": ["A study of learning"],
            "author": [{"given": "Ana", "family": "Silva"}],
            "published-print": {"date-parts": [[2024, 5, 1]]},
            "DOI": "10.1234/example",
            "container-title": ["Journal of Tests"],
            "publisher": "Example Press",
            "type": "journal-article",
        }]}}
        with patch("nexus_learning.crossref.urllib.request.urlopen", return_value=FakeResponse(payload)) as mocked:
            results = CrossrefClient(mailto="dev@example.org").search("learning", 3)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "A study of learning")
        self.assertEqual(results[0]["authors"], ["Ana Silva"])
        self.assertEqual(results[0]["year"], 2024)
        self.assertEqual(results[0]["url"], "https://doi.org/10.1234/example")
        request = mocked.call_args.args[0]
        self.assertIn("mailto=dev%40example.org", request.full_url)
        self.assertEqual(mocked.call_args.kwargs["timeout"], 12)

    def test_empty_query_and_invalid_limit_rejected(self):
        client = CrossrefClient()
        with self.assertRaises(ValueError):
            client.search(" ")
        with self.assertRaises(ValueError):
            client.search("science", 21)

    def test_network_failure_is_wrapped(self):
        with patch("nexus_learning.crossref.urllib.request.urlopen", side_effect=OSError("offline")):
            with self.assertRaises(CrossrefError):
                CrossrefClient().search("science")

    def test_malformed_payload_is_rejected(self):
        with patch("nexus_learning.crossref.urllib.request.urlopen", return_value=FakeResponse({"oops": {}})):
            with self.assertRaises(CrossrefError):
                CrossrefClient().search("science")


if __name__ == "__main__":
    unittest.main()
