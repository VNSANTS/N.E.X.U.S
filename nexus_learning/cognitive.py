"""Consent-based cognitive adaptation profile for N.E.X.U.S.

Stores explicit interaction preferences and user-reviewed reasoning patterns.
It does not diagnose personality, infer sensitive traits, or learn from raw
conversation transcripts automatically.
"""
import re

from .engine import now, uid


PREFERENCE_VALUES = {
    "response_length": {"short", "medium", "long"},
    "explanation_style": {"direct", "step_by_step", "conceptual"},
    "challenge_level": {"gentle", "balanced", "demanding"},
    "disagreement_style": {"candid", "gentle"},
}
PATTERN_STATES = {"proposed", "confirmed", "rejected"}


class CognitiveAdaptation:
    """Opt-in store and prompt-context builder for cognitive adaptation."""

    def __init__(self, engine):
        self.engine = engine
        with self.engine.db() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS cognitive_settings(
              key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cognitive_preferences(
              key TEXT PRIMARY KEY, value TEXT NOT NULL, source TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cognitive_patterns(
              id TEXT PRIMARY KEY, pattern TEXT NOT NULL, rationale TEXT NOT NULL,
              confidence REAL NOT NULL, status TEXT NOT NULL,
              review_rationale TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_cognitive_patterns_status
              ON cognitive_patterns(status, updated_at);
            """)
            c.execute(
                "INSERT OR IGNORE INTO cognitive_settings VALUES('enabled','false',?)",
                (now(),),
            )

    def enabled(self):
        with self.engine.db() as c:
            row = c.execute(
                "SELECT value FROM cognitive_settings WHERE key='enabled'"
            ).fetchone()
        return bool(row and row["value"] == "true")

    def set_enabled(self, enabled):
        if not isinstance(enabled, bool):
            raise ValueError("enabled must be a boolean")
        with self.engine.db() as c:
            c.execute(
                """INSERT INTO cognitive_settings VALUES('enabled',?,?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value,
                   updated_at=excluded.updated_at""",
                ("true" if enabled else "false", now()),
            )
            self.engine._audit(c, "cognitive.enabled" if enabled else "cognitive.disabled",
                               "cognitive_profile", "primary")
        return self.enabled()

    def set_preference(self, key, value, source="user"):
        if key not in PREFERENCE_VALUES:
            raise ValueError("unsupported preference")
        if not isinstance(value, str) or value not in PREFERENCE_VALUES[key]:
            raise ValueError("unsupported value for preference")
        if source != "user":
            raise ValueError("preferences must be explicitly supplied by the user")
        stamp = now()
        with self.engine.db() as c:
            c.execute(
                """INSERT INTO cognitive_preferences VALUES(?,?,?,?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value,
                   source=excluded.source,updated_at=excluded.updated_at""",
                (key, value, source, stamp),
            )
            self.engine._audit(c, "cognitive.preference_set", "cognitive_preference",
                               key, {"value": value, "source": source})
        return {"key": key, "value": value, "source": source}

    def list_preferences(self):
        with self.engine.db() as c:
            return [dict(r) for r in c.execute(
                "SELECT key,value,source,updated_at FROM cognitive_preferences ORDER BY key"
            ).fetchall()]

    def propose_pattern(self, pattern, rationale, confidence=0.5):
        if not isinstance(pattern, str) or not pattern.strip():
            raise ValueError("pattern cannot be empty")
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError("rationale cannot be empty")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        clean_pattern = re.sub(r"\s+", " ", pattern).strip()
        stamp, pattern_id = now(), uid("cog")
        with self.engine.db() as c:
            existing = c.execute(
                "SELECT id FROM cognitive_patterns WHERE lower(pattern)=lower(?) "
                "AND status='proposed'", (clean_pattern,)
            ).fetchone()
            if existing:
                raise ValueError("an equivalent proposed pattern already exists")
            c.execute(
                "INSERT INTO cognitive_patterns VALUES(?,?,?,?, 'proposed',NULL,?,?)",
                (pattern_id, clean_pattern, rationale.strip(), float(confidence), stamp, stamp),
            )
            self.engine._audit(c, "cognitive.pattern_proposed", "cognitive_pattern",
                               pattern_id, {"confidence": float(confidence)})
        return pattern_id

    def review_pattern(self, pattern_id, status, rationale):
        if status not in {"confirmed", "rejected"}:
            raise ValueError("status must be confirmed or rejected")
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError("review rationale is required")
        with self.engine.db() as c:
            cur = c.execute(
                """UPDATE cognitive_patterns SET status=?,review_rationale=?,updated_at=?
                   WHERE id=? AND status='proposed'""",
                (status, rationale.strip(), now(), pattern_id),
            )
            if cur.rowcount != 1:
                exists = c.execute(
                    "SELECT 1 FROM cognitive_patterns WHERE id=?", (pattern_id,)
                ).fetchone()
                if not exists:
                    raise KeyError(pattern_id)
                raise ValueError("only proposed patterns can be reviewed")
            self.engine._audit(c, "cognitive.pattern_" + status, "cognitive_pattern",
                               pattern_id, {"rationale": rationale.strip()})
        return self.get_pattern(pattern_id)

    def get_pattern(self, pattern_id):
        with self.engine.db() as c:
            row = c.execute(
                "SELECT * FROM cognitive_patterns WHERE id=?", (pattern_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_patterns(self, status=None):
        if status is not None and status not in PATTERN_STATES:
            raise ValueError("invalid pattern status")
        with self.engine.db() as c:
            if status:
                rows = c.execute(
                    "SELECT * FROM cognitive_patterns WHERE status=? ORDER BY updated_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM cognitive_patterns ORDER BY updated_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def build_context(self):
        """Return a small prompt fragment; empty unless the user opted in."""
        if not self.enabled():
            return ""
        preferences = self.list_preferences()
        patterns = self.list_patterns("confirmed")
        if not preferences and not patterns:
            return ""
        lines = [
            "Cognitive adaptation guidance (user-controlled; not a psychological diagnosis):",
            "- Use these as revisable collaboration preferences, not fixed traits.",
            "- Do not merely agree or imitate; add missing perspectives and challenge weak reasoning respectfully.",
            "- If current instructions conflict with this profile, follow the current instructions.",
        ]
        if preferences:
            lines.append("Explicit user preferences:")
            lines.extend(f"- {p['key']}: {p['value']}" for p in preferences)
        if patterns:
            lines.append("User-reviewed reasoning patterns:")
            lines.extend(f"- {p['pattern']} (confidence recorded: {p['confidence']:.2f})"
                         for p in patterns)
        return "\n".join(lines)
