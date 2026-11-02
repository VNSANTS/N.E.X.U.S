"""Bounded retrieval of active memories and sourced, validated claims."""
import re


class ContextRetriever:
    def __init__(self, engine, *, max_chars=3500, max_items=8, semantic_index=None):
        self.engine = engine
        self.max_chars = max_chars
        self.max_items = max_items
        self.semantic_index = semantic_index

    @staticmethod
    def _terms(query):
        return list(dict.fromkeys(w for w in re.findall(r"[\w-]{3,}", query.lower()) if w))[:8]

    def retrieve(self, query):
        terms = self._terms(query)
        if not terms:
            return []
        conditions = " OR ".join("(title LIKE ? OR body LIKE ?)" for _ in terms)
        args = [v for term in terms for v in (f"%{term}%", f"%{term}%")]
        with self.engine.db() as c:
            memories = c.execute(
                f"SELECT id,kind,title,body FROM memories WHERE status='active' AND ({conditions}) ORDER BY updated_at DESC LIMIT ?",
                (*args, self.max_items),
            ).fetchall()
            claim_conditions = " OR ".join("cl.claim LIKE ?" for _ in terms)
            claim_args = [f"%{term}%" for term in terms]
            claims = c.execute(f"""SELECT cl.id,cl.claim,cl.confidence,s.uri,s.title AS source_title,cs.excerpt
              FROM claims cl JOIN claim_sources cs ON cs.claim_id=cl.id
              JOIN sources s ON s.id=cs.source_id
              WHERE cl.state='validated' AND ({claim_conditions})
              ORDER BY cl.confidence DESC,cl.updated_at DESC LIMIT ?""",
              (*claim_args, self.max_items)).fetchall()
        results = []
        if self.semantic_index is not None:
            try:
                results.extend(self.semantic_index.search(query, limit=self.max_items))
            except Exception:
                # Provider/embedding failures must not block the lexical path.
                pass
        seen_memory_ids = {item["id"] for item in results if item.get("kind") == "memory"}
        for row in memories:
            if row["id"] not in seen_memory_ids:
                results.append({"kind": "memory", "id": row["id"], "text":
                                f"[{row['kind']} memory {row['id']}] {row['title']}: {row['body']}"})
        for row in claims:
            excerpt = (row["excerpt"] or "")[:500]
            results.append({"kind": "validated_claim", "id": row["id"], "text":
                            f"[validated claim {row['id']}, confidence {row['confidence']}; source {row['uri']} "
                            f"{row['source_title']}; excerpt: {excerpt}] {row['claim']}"})
        bounded, used = [], 0
        for item in results:
            text = item["text"][:self.max_chars - used]
            if not text:
                break
            bounded.append({**item, "text": text})
            used += len(text)
            if used >= self.max_chars:
                break
        return bounded
