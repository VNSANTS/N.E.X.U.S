"""Small, dependency-free client for scholarly metadata from Crossref.

This module retrieves metadata only. It does not download full papers or validate claims.
"""
import json
import urllib.error
import urllib.parse
import urllib.request


API_BASE = "https://api.crossref.org/works"
DEFAULT_TIMEOUT = 12
MAX_RESULTS = 20


class CrossrefError(RuntimeError):
    """Raised when Crossref cannot provide a usable response."""


class CrossrefClient:
    def __init__(self, mailto=None, timeout=DEFAULT_TIMEOUT, user_agent="N.E.X.U.S./0.1 (scholarly metadata client)"):
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.mailto = mailto.strip() if isinstance(mailto, str) and mailto.strip() else None
        self.timeout = timeout
        self.user_agent = user_agent

    @staticmethod
    def _first(value):
        return value[0] if isinstance(value, list) and value else ""

    @classmethod
    def _normalize(cls, item):
        title = cls._first(item.get("title"))
        authors = []
        for author in item.get("author", [])[:12]:
            name = " ".join(part for part in (author.get("given"), author.get("family")) if part)
            if name:
                authors.append(name)
        date_parts = item.get("published-print", {}).get("date-parts") or item.get("published-online", {}).get("date-parts") or item.get("created", {}).get("date-parts") or []
        date = date_parts[0] if date_parts else []
        year = date[0] if date else None
        doi = item.get("DOI", "")
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        return {
            "title": title,
            "authors": authors,
            "year": year,
            "doi": doi,
            "url": url,
            "container_title": cls._first(item.get("container-title")),
            "publisher": item.get("publisher", ""),
            "type": item.get("type", ""),
            "score": item.get("score"),
            "source": "Crossref",
        }

    def search(self, query, limit=10):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must not be empty")
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            raise ValueError("limit must be an integer") from None
        if not 1 <= limit <= MAX_RESULTS:
            raise ValueError(f"limit must be between 1 and {MAX_RESULTS}")

        params = {"query": query.strip(), "rows": limit}
        if self.mailto:
            params["mailto"] = self.mailto
        url = API_BASE + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": self.user_agent},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise CrossrefError(f"Crossref request failed: {exc}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CrossrefError("Crossref returned invalid JSON") from exc

        try:
            items = payload["message"]["items"]
        except (KeyError, TypeError):
            raise CrossrefError("Crossref response is missing message.items") from None
        return [self._normalize(item) for item in items if isinstance(item, dict)]
