"""Central capability policy for the personal N.E.X.U.S. agent.

The owner may grant broad access to ordinary modules. High-impact actions are
never silently authorized by a blanket grant: they require a fresh confirmation.
This module does not create OS, account, browser, or provider credentials.
"""
from datetime import datetime, timezone


STANDARD_SCOPES = frozenset({
    "memory.read", "memory.write", "cognitive.read", "cognitive.write",
    "research.web", "knowledge.read", "knowledge.write", "skills.read",
    "skills.create", "agents.run", "tools.use", "files.read",
    "files.write", "local.execute", "projects.read", "projects.write",
})
CONFIRM_SCOPES = frozenset({
    "external.send", "external.publish", "external.delete",
    "system.install", "system.modify", "security.change",
    "credentials.read", "data.export",
})
ALL_SCOPES = STANDARD_SCOPES | CONFIRM_SCOPES


def _now():
    return datetime.now(timezone.utc).isoformat()


class PermissionManager:
    """SQLite-backed, auditable scopes for N.E.X.U.S. modules."""

    def __init__(self, engine):
        self.engine = engine
        with engine.db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS nexus_permissions(
              scope TEXT PRIMARY KEY, granted INTEGER NOT NULL,
              updated_at TEXT NOT NULL, source TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS nexus_permission_audit(
              id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL,
              decision TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL
            );
            """)

    def grant_standard_access(self):
        """Enable all ordinary modules; high-impact scopes remain confirmation-only."""
        stamp = _now()
        with self.engine.db() as db:
            for scope in sorted(STANDARD_SCOPES):
                db.execute("""
                    INSERT INTO nexus_permissions VALUES(?,1,?,'owner_bulk_grant')
                    ON CONFLICT(scope) DO UPDATE SET granted=1,
                    updated_at=excluded.updated_at,source=excluded.source
                """, (scope, stamp))
            self._audit(db, "standard_access_granted",
                        "Owner enabled all standard N.E.X.U.S. capabilities.")
        return self.status()

    def grant(self, scope):
        self._validate_scope(scope)
        if scope in CONFIRM_SCOPES:
            raise PermissionError(
                "This scope requires a fresh, action-specific confirmation; "
                "it cannot be enabled by a permanent blanket grant."
            )
        with self.engine.db() as db:
            db.execute("""
                INSERT INTO nexus_permissions VALUES(?,1,?,'owner')
                ON CONFLICT(scope) DO UPDATE SET granted=1,
                updated_at=excluded.updated_at,source='owner'
            """, (scope, _now()))
            self._audit(db, "scope_granted", scope)
        return True

    def revoke(self, scope):
        self._validate_scope(scope)
        with self.engine.db() as db:
            db.execute("""
                INSERT INTO nexus_permissions VALUES(?,0,?,'owner')
                ON CONFLICT(scope) DO UPDATE SET granted=0,
                updated_at=excluded.updated_at,source='owner'
            """, (scope, _now()))
            self._audit(db, "scope_revoked", scope)
        return True

    def authorize(self, scope, *, confirmed=False):
        """Check a capability immediately before use.

        confirmed=True must only come from a trusted interactive confirmation
        for the exact pending action, never from an agent-generated plan.
        """
        self._validate_scope(scope)
        with self.engine.db() as db:
            row = db.execute(
                "SELECT granted FROM nexus_permissions WHERE scope=?", (scope,)
            ).fetchone()
            granted = bool(row and row["granted"])
            if scope in CONFIRM_SCOPES:
                allowed = bool(confirmed)
                decision = "confirmed_once" if allowed else "confirmation_required"
            else:
                allowed = granted
                decision = "allowed" if allowed else "denied"
            self._audit(db, decision, scope)
        return allowed

    def require(self, scope, *, confirmed=False):
        if not self.authorize(scope, confirmed=confirmed):
            if scope in CONFIRM_SCOPES:
                raise PermissionError(f"Fresh confirmation required for: {scope}")
            raise PermissionError(f"Capability not granted: {scope}")

    def status(self):
        with self.engine.db() as db:
            rows = db.execute(
                "SELECT scope,granted,updated_at,source FROM nexus_permissions ORDER BY scope"
            ).fetchall()
        granted = {r["scope"]: dict(r) for r in rows if r["granted"]}
        return {
            "standard_scopes": sorted(STANDARD_SCOPES),
            "granted": sorted(granted),
            "not_granted": sorted(STANDARD_SCOPES - set(granted)),
            "confirmation_required": sorted(CONFIRM_SCOPES),
        }

    def audit_log(self, limit=100):
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        with self.engine.db() as db:
            rows = db.execute(
                "SELECT scope,decision,reason,created_at FROM nexus_permission_audit "
                "ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _validate_scope(scope):
        if scope not in ALL_SCOPES:
            raise ValueError(f"Unknown capability scope: {scope}")

    @staticmethod
    def _audit(db, decision, reason):
        db.execute(
            "INSERT INTO nexus_permission_audit(scope,decision,reason,created_at) "
            "VALUES('system',?,?,?)", (decision, reason, _now())
        )
