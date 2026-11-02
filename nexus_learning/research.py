"""Extensible metadata discovery. This adapter never fetches article URLs or full text."""
import hashlib
import json
from datetime import datetime, timezone
from typing import Protocol

from .discovery import CrossrefDiscovery
from .integrations import is_public_http_url
from .engine import now, uid


class DiscoveryAdapter(Protocol):
    name: str
    def search(self, query: str, limit: int = 5) -> list[dict]: ...


class ResearchService:
    """Stores traceable discovery metadata and short, attributed abstract excerpts."""

    def __init__(self, engine, adapter=None, *, min_interval_seconds=1):
        self.engine = engine
        self.adapter = adapter or CrossrefDiscovery()
        self.min_interval_seconds = min_interval_seconds
        with engine.db() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS research_records(
              id TEXT PRIMARY KEY,provider TEXT NOT NULL,external_id TEXT NOT NULL,
              source_id TEXT NOT NULL REFERENCES sources(id),title TEXT NOT NULL,
              authors_json TEXT NOT NULL,publication_date TEXT,abstract_excerpt TEXT NOT NULL,
              abstract_rights TEXT NOT NULL,source_class TEXT NOT NULL,metadata_json TEXT NOT NULL,
              content_hash TEXT NOT NULL,
              retrieved_at TEXT NOT NULL,UNIQUE(provider,external_id));
            CREATE TABLE IF NOT EXISTS cycle_research_items(
              cycle_id TEXT NOT NULL,record_id TEXT NOT NULL REFERENCES research_records(id),
              PRIMARY KEY(cycle_id,record_id));
            CREATE TABLE IF NOT EXISTS research_request_log(
              id TEXT PRIMARY KEY,provider TEXT NOT NULL,query_hash TEXT NOT NULL,
              status TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_research_records_date ON research_records(publication_date);
            """)

    def search_and_store(self, cycle_id, query, limit=5):
        if not isinstance(query, str) or not query.strip() or len(query) > 250:
            raise ValueError("research query must contain 1 to 250 characters")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 10:
            raise ValueError("research result limit must be between 1 and 10")
        query_hash = hashlib.sha256(query.strip().casefold().encode("utf-8")).hexdigest()
        now_dt = datetime.now(timezone.utc)
        with self.engine.db() as c:
            c.execute("BEGIN IMMEDIATE")
            last = c.execute("SELECT created_at FROM research_request_log WHERE provider=? ORDER BY created_at DESC LIMIT 1",
                             (self.adapter.name,)).fetchone()
            if last:
                previous = datetime.fromisoformat(last["created_at"])
                if (now_dt - previous).total_seconds() < self.min_interval_seconds:
                    raise RuntimeError("research rate limit cooldown")
            sent_at = now_dt.isoformat(timespec="seconds")
            request_id = uid("rrq")
            c.execute("INSERT INTO research_request_log VALUES(?,?,?,'sent',?)",
                      (request_id, self.adapter.name, query_hash, sent_at))
        try:
            results = self.adapter.search(query.strip(), limit)
        except Exception:
            with self.engine.db() as c:
                c.execute("UPDATE research_request_log SET status='failed' WHERE id=?", (request_id,))
            raise
        stored, seen = [], set()
        for item in results:
            if not isinstance(item, dict):
                continue
            provider = item.get("provider") if isinstance(item.get("provider"), str) else self.adapter.name
            external_id = (item.get("doi") or item.get("external_id") or item.get("url") or "").strip()
            title = item.get("title") if isinstance(item.get("title"), str) else ""
            url = item.get("url") if isinstance(item.get("url"), str) else ""
            if (not external_id or not title or not url or external_id in seen
                    or not is_public_http_url(url)):
                continue
            seen.add(external_id)
            authors = item.get("authors") if isinstance(item.get("authors"), list) else []
            authors = [x[:200] for x in authors if isinstance(x, str)][:20]
            abstract = item.get("abstract") if isinstance(item.get("abstract"), str) else ""
            excerpt = " ".join(abstract.split())[:1200]
            publication_date = item.get("publication_date")
            if not isinstance(publication_date, str):
                year = item.get("year")
                publication_date = f"{year:04d}" if isinstance(year, int) and 1000 <= year <= 9999 else None
            digest = hashlib.sha256(json.dumps(item, ensure_ascii=False, sort_keys=True,
                                               default=str).encode("utf-8")).hexdigest()
            with self.engine.db() as c:
                existing = c.execute("SELECT id FROM research_records WHERE provider=? AND external_id=?",
                                     (provider, external_id)).fetchone()
            if existing:
                record_id = existing["id"]
            else:
                source_id = self.engine.add_source(url, title)
                with self.engine.db() as c:
                    c.execute("UPDATE sources SET metadata=? WHERE id=?",
                              (json.dumps({"provider": provider, "untrusted": True,
                                           "external_id": external_id}, sort_keys=True), source_id))
                record_id = uid("rr")
                with self.engine.db() as c:
                    c.execute("INSERT INTO research_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (record_id, provider, external_id, source_id, title,
                               json.dumps(authors, ensure_ascii=False), publication_date,
                               excerpt, ("publisher_or_author_copyright_possible" if item.get("doi") or provider == "crossref" else "source_site_rights_apply"),
                               item.get("source_class") or ("crossref_deposited_metadata" if item.get("doi") or provider == "crossref" else "web_search_result_untrusted"),
                               json.dumps({"publisher": item.get("publisher"),
                                           "container_title": item.get("container_title"),
                                           "record_type": item.get("type"),
                                           "year": item.get("year"),
                                           "relevance_score": item.get("score"),
                                           "content_is_untrusted": True,
                                           "reliability_classification": "deposited_metadata_not_truth_validation" if provider == "crossref" else "search_result_not_truth_validation"},
                                          ensure_ascii=False, sort_keys=True), digest, now()))
            with self.engine.db() as c:
                c.execute("INSERT OR IGNORE INTO cycle_research_items VALUES(?,?)", (cycle_id, record_id))
            stored.append(record_id)
        return stored

    def for_cycle(self, cycle_id):
        with self.engine.db() as c:
            return [dict(r) for r in c.execute("""SELECT rr.*,s.uri,s.title AS source_title
              FROM cycle_research_items cri JOIN research_records rr ON rr.id=cri.record_id
              JOIN sources s ON s.id=rr.source_id WHERE cri.cycle_id=? ORDER BY rr.publication_date DESC""",
              (cycle_id,)).fetchall()]

    def list(self, limit=100):
        with self.engine.db() as c:
            return [dict(r) for r in c.execute("""SELECT rr.*,s.uri FROM research_records rr
              JOIN sources s ON s.id=rr.source_id ORDER BY retrieved_at DESC LIMIT ?""",
              (max(1, min(int(limit), 500)),)).fetchall()]
