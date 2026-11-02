"""Bounded, explainable retrieval of active memories and validated sourced claims."""
import re


class ContextRetriever:
    MAX_ITEMS = 50
    MAX_CHARS = 20_000

    def __init__(self, engine, *, max_chars=3500, max_items=8, semantic_index=None):
        if isinstance(max_chars, bool) or not isinstance(max_chars, int) or not 128 <= max_chars <= self.MAX_CHARS:
            raise ValueError("max_chars must be between 128 and 20000")
        if isinstance(max_items, bool) or not isinstance(max_items, int) or not 1 <= max_items <= self.MAX_ITEMS:
            raise ValueError("max_items must be between 1 and 50")
        self.engine = engine
        self.max_chars = max_chars
        self.max_items = max_items
        self.semantic_index = semantic_index

    @staticmethod
    def _terms(query):
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        return list(dict.fromkeys(w for w in re.findall(r"[\w-]{3,}", query.casefold()) if w))[:8]

    @staticmethod
    def _score(text, terms, title=""):
        body = (text or "").casefold()
        heading = (title or "").casefold()
        matched = [term for term in terms if term in body]
        title_matches = [term for term in terms if term in heading]
        return len(matched) + 2 * len(title_matches), matched

    def retrieve_detailed(self, query, *, include_semantic=True):
        terms = self._terms(query)
        if not terms:
            return {"items": [], "query_terms": [], "lexical_candidates": 0,
                    "semantic_candidates": 0, "used_semantic": False,
                    "truncated": False, "chars_used": 0}
        conditions = " OR ".join("(title LIKE ? OR body LIKE ?)" for _ in terms)
        args = [value for term in terms for value in (f"%{term}%", f"%{term}%")]
        claim_conditions = " OR ".join("cl.claim LIKE ?" for _ in terms)
        claim_args = [f"%{term}%" for term in terms]
        with self.engine.db() as c:
            memories = [dict(row) for row in c.execute(
                f"""SELECT id,kind,title,body,updated_at FROM memories
                    WHERE status='active' AND ({conditions})
                    ORDER BY updated_at DESC LIMIT ?""", (*args, self.max_items * 5))]
            claim_rows = [dict(row) for row in c.execute(f"""
                SELECT cl.id,cl.claim,cl.confidence,cl.updated_at,
                       s.id AS source_id,s.uri,s.title AS source_title,cs.excerpt
                FROM claims cl JOIN claim_sources cs ON cs.claim_id=cl.id
                JOIN sources s ON s.id=cs.source_id
                WHERE cl.state='validated' AND ({claim_conditions})
                ORDER BY cl.confidence DESC,cl.updated_at DESC LIMIT ?""",
                (*claim_args, self.max_items * 10))]
        ranked = []
        for row in memories:
            score, matched = self._score(row["body"], terms, row["title"])
            ranked.append({"kind": "memory", "id": row["id"], "score": score,
                           "matched_terms": matched, "retrieval_method": "lexical",
                           "text": f"[{row['kind']} memory {row['id']}] {row['title']}: {row['body']}"})
        grouped = {}
        for row in claim_rows:
            grouped.setdefault(row["id"], {"claim": row["claim"], "confidence": row["confidence"],
                "sources": [], "updated_at": row["updated_at"]})
            grouped[row["id"]]["sources"].append(row)
        for claim_id, item in grouped.items():
            score, matched = self._score(item["claim"], terms)
            source_text = " | ".join(
                f"{source['uri']} ({source['source_title']}); excerpt: {(source['excerpt'] or '')[:350]}"
                for source in item["sources"])
            ranked.append({"kind": "validated_claim", "id": claim_id, "score": score,
                "matched_terms": matched, "retrieval_method": "lexical",
                "text": f"[validated claim {claim_id}, confidence {item['confidence']}; {source_text}] {item['claim']}"})
        lexical_count = len(ranked)
        semantic_count = 0
        if include_semantic and self.semantic_index is not None:
            try:
                semantic = self.semantic_index.search(query, limit=self.max_items)
                semantic_count = len(semantic)
                known = {item["id"] for item in ranked if item["kind"] == "memory"}
                for item in semantic:
                    if item.get("kind") == "memory" and item.get("id") not in known:
                        ranked.append({**item, "matched_terms": [], "retrieval_method": "semantic"})
                        known.add(item["id"])
            except Exception:
                # Semantic providers are optional; lexical retrieval remains available.
                pass
        ranked.sort(key=lambda item: (item["score"], item.get("kind") == "validated_claim"), reverse=True)
        selected = ranked[:self.max_items]
        bounded, used, truncated = [], 0, len(ranked) > len(selected)
        for item in selected:
            remaining = self.max_chars - used
            if remaining <= 0:
                truncated = True
                break
            rendered = item["text"][:remaining]
            if len(rendered) < len(item["text"]):
                truncated = True
            bounded.append({**item, "text": rendered})
            used += len(rendered)
        return {"items": bounded, "query_terms": terms,
                "lexical_candidates": lexical_count,
                "semantic_candidates": semantic_count,
                "used_semantic": any(x.get("retrieval_method") == "semantic" for x in bounded),
                "truncated": truncated, "chars_used": used}

    def retrieve(self, query):
        """Compatibility API: return only bounded context items."""
        return self.retrieve_detailed(query)["items"]
