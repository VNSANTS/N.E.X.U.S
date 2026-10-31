"""Bounded, provenance-preserving text ingestion for the N.E.X.U.S. learning core.

Only plain text and Markdown are supported. No network access or LLM calls occur here.
"""
import hashlib
import re
from pathlib import Path

from .engine import now, uid

MAX_DOCUMENT_BYTES = 1_000_000
ALLOWED_SUFFIXES = {".txt", ".md", ".markdown"}
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_OVERLAP = 150


class DocumentIngestor:
    def __init__(self, engine, max_bytes=MAX_DOCUMENT_BYTES):
        self.engine = engine
        self.max_bytes = max_bytes
        with self.engine.db() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS documents(
              id TEXT PRIMARY KEY,
              source_id TEXT NOT NULL UNIQUE REFERENCES sources(id) ON DELETE RESTRICT,
              content_hash TEXT NOT NULL UNIQUE,
              content_type TEXT NOT NULL,
              char_count INTEGER NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS document_chunks(
              id TEXT PRIMARY KEY,
              document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
              chunk_index INTEGER NOT NULL,
              start_char INTEGER NOT NULL,
              end_char INTEGER NOT NULL,
              content TEXT NOT NULL,
              UNIQUE(document_id, chunk_index)
            );
            CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id, chunk_index);
            """)

    @staticmethod
    def _clean(text):
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
        return "\n".join(line.rstrip() for line in text.split("\n")).strip()

    @staticmethod
    def _split(text, chunk_size, overlap):
        if chunk_size < 100 or overlap < 0 or overlap >= chunk_size:
            raise ValueError("chunk_size must be >= 100 and overlap must be smaller")
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                boundary = text.rfind("\n", start + chunk_size // 2, end)
                if boundary > start:
                    end = boundary
            piece = text[start:end].strip()
            if piece:
                left_trim = len(text[start:end]) - len(text[start:end].lstrip())
                chunks.append((start + left_trim, start + left_trim + len(piece), piece))
            if end >= len(text):
                break
            start = max(start + 1, end - overlap)
        return chunks

    def ingest_text(self, text, uri, title="", content_type="text/plain",
                    chunk_size=DEFAULT_CHUNK_SIZE, overlap=DEFAULT_OVERLAP):
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        cleaned = self._clean(text)
        if not cleaned:
            raise ValueError("document is empty after text normalization")
        raw = cleaned.encode("utf-8")
        if len(raw) > self.max_bytes:
            raise ValueError(f"document exceeds the {self.max_bytes}-byte limit")
        digest = hashlib.sha256(raw).hexdigest()
        pieces = self._split(cleaned, chunk_size, overlap)
        with self.engine.db() as c:
            existing = c.execute(
                "SELECT d.id,d.source_id,d.content_hash,d.char_count,s.uri,s.title "
                "FROM documents d JOIN sources s ON s.id=d.source_id WHERE d.content_hash=?",
                (digest,)).fetchone()
            if existing:
                return {"document_id": existing["id"], "source_id": existing["source_id"],
                        "duplicate": True, "chunks": c.execute(
                            "SELECT COUNT(*) FROM document_chunks WHERE document_id=?",
                            (existing["id"],)).fetchone()[0]}
            source_id, document_id, stamp = uid("src"), uid("doc"), now()
            c.execute("INSERT INTO sources VALUES(?,?,?,?,?)",
                      (source_id, uri.strip(), title.strip(), stamp, "{}"))
            c.execute("INSERT INTO documents VALUES(?,?,?,?,?,?)",
                      (document_id, source_id, digest, content_type, len(cleaned), stamp))
            for index, (start, end, piece) in enumerate(pieces):
                c.execute("INSERT INTO document_chunks VALUES(?,?,?,?,?,?)",
                          (uid("chunk"), document_id, index, start, end, piece))
            self.engine._audit(c, "document.ingested", "document", document_id,
                               {"source_id": source_id, "sha256": digest,
                                "chunks": len(pieces), "char_count": len(cleaned)})
        return {"document_id": document_id, "source_id": source_id,
                "duplicate": False, "chunks": len(pieces), "sha256": digest}

    def ingest_file(self, path):
        file_path = Path(path).expanduser()
        if file_path.suffix.lower() not in ALLOWED_SUFFIXES:
            raise ValueError("only .txt, .md and .markdown files are supported")
        if not file_path.is_file():
            raise FileNotFoundError(str(file_path))
        if file_path.stat().st_size > self.max_bytes:
            raise ValueError(f"file exceeds the {self.max_bytes}-byte limit")
        raw = file_path.read_bytes()
        if len(raw) > self.max_bytes:
            raise ValueError(f"file exceeds the {self.max_bytes}-byte limit")
        text = raw.decode("utf-8-sig")
        content_type = "text/markdown" if file_path.suffix.lower() in {".md", ".markdown"} else "text/plain"
        return self.ingest_text(text, str(file_path.resolve()), file_path.name, content_type)

    def search(self, query, limit=10):
        terms = list(dict.fromkeys(re.findall(r"[\wÀ-ÿ]{2,}", query.lower(), flags=re.UNICODE)))
        if not terms:
            return []
        with self.engine.db() as c:
            rows = [dict(r) for r in c.execute("""
              SELECT dc.id AS chunk_id,dc.document_id,dc.chunk_index,
                     dc.start_char,dc.end_char,dc.content,
                     d.content_hash,d.content_type,d.char_count,
                     s.id AS source_id,s.uri,s.title
              FROM document_chunks dc
              JOIN documents d ON d.id=dc.document_id
              JOIN sources s ON s.id=d.source_id
            """).fetchall()]
        for row in rows:
            haystack = row["content"].lower()
            row["score"] = sum(haystack.count(term) for term in terms)
        matches = [r for r in rows if r["score"] > 0]
        matches.sort(key=lambda r: (-r["score"], r["document_id"], r["chunk_index"]))
        return matches[:max(1, min(int(limit), 100))]
