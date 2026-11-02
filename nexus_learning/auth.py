"""Local password authentication and opaque bearer tokens for the API."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from .engine import now, uid

ITERATIONS = 310_000
TOKEN_LIFETIME = timedelta(hours=12)


def _password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)


class AuthStore:
    def __init__(self, engine):
        self.engine = engine
        with engine.db() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS api_users(
              id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE,
              salt BLOB NOT NULL, password_hash BLOB NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS api_tokens(
              token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES api_users(id) ON DELETE CASCADE,
              expires_at TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_api_tokens_expiry ON api_tokens(expires_at);
            CREATE TRIGGER IF NOT EXISTS api_users_single_owner
              BEFORE INSERT ON api_users WHEN EXISTS(SELECT 1 FROM api_users)
              BEGIN SELECT RAISE(ABORT, 'N.E.X.U.S. supports one local owner account'); END;
            """)

    def has_users(self):
        with self.engine.db() as c:
            return c.execute("SELECT 1 FROM api_users LIMIT 1").fetchone() is not None

    def create_user(self, username, password):
        if not isinstance(username, str) or not username.strip() or len(username) > 80:
            raise ValueError("username must contain 1 to 80 characters")
        if not isinstance(password, str) or len(password) < 14 or len(password) > 1024 or not password.strip():
            raise ValueError("password must contain 14 to 1024 characters")
        salt = secrets.token_bytes(16)
        with self.engine.db() as c:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT 1 FROM api_users LIMIT 1").fetchone():
                raise ValueError("only one local owner account is supported")
            c.execute("INSERT INTO api_users VALUES(?,?,?,?,?)",
                      (uid("usr"), username.strip(), salt, _password_hash(password, salt), now()))

    def login(self, username, password):
        if (not isinstance(username, str) or len(username) > 80
                or not isinstance(password, str) or len(password) > 1024):
            return None
        with self.engine.db() as c:
            row = c.execute("SELECT * FROM api_users WHERE username=?", (username,)).fetchone()
        # Perform a PBKDF2 even for unknown usernames to reduce timing disclosure.
        salt = row["salt"] if row else b"\0" * 16
        candidate = _password_hash(password if isinstance(password, str) else "", salt)
        if not row or not hmac.compare_digest(candidate, row["password_hash"]):
            return None
        token = secrets.token_urlsafe(32)
        expires = (datetime.now(timezone.utc) + TOKEN_LIFETIME).isoformat(timespec="seconds")
        with self.engine.db() as c:
            c.execute("INSERT INTO api_tokens VALUES(?,?,?,?)",
                      (hashlib.sha256(token.encode()).hexdigest(), row["id"], expires, now()))
        return {"access_token": token, "token_type": "Bearer", "expires_at": expires}

    def user_for_token(self, token):
        if not token or len(token) > 256:
            return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.engine.db() as c:
            row = c.execute("""SELECT u.id,u.username,t.expires_at FROM api_tokens t
                JOIN api_users u ON u.id=t.user_id WHERE t.token_hash=?""", (digest,)).fetchone()
            if row and row["expires_at"] > now():
                return {"id": row["id"], "username": row["username"]}
            if row:
                c.execute("DELETE FROM api_tokens WHERE token_hash=?", (digest,))
        return None

    def revoke(self, token):
        if not token:
            return
        with self.engine.db() as c:
            c.execute("DELETE FROM api_tokens WHERE token_hash=?",
                      (hashlib.sha256(token.encode()).hexdigest(),))
