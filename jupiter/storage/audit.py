"""Jupiter audit store — local audit log (SQLite)."""
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional
from jupiter.config import AUDIT_DB_PATH, ensure_dirs


class AuditStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or AUDIT_DB_PATH
        ensure_dirs()
        self._init_schema()

    def _conn(self):
        return sqlite3.connect(self.path)

    def _init_schema(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY, action TEXT NOT NULL, scope TEXT, details TEXT, outcome TEXT, created_at REAL NOT NULL);
            """)

    def log(self, action: str, scope: Optional[str] = None, details: Optional[dict] = None, outcome: Optional[str] = None):
        with self._conn() as c:
            c.execute("INSERT INTO audit (action, scope, details, outcome, created_at) VALUES (?, ?, ?, ?, ?)",
                      (action, scope, json.dumps(details or {}), outcome, time.time()))

    def get_recent(self, limit: int = 100):
        with self._conn() as c:
            rows = c.execute("SELECT action, scope, details, outcome, created_at FROM audit ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"action": r[0], "scope": r[1], "details": json.loads(r[2] or "{}"), "outcome": r[3], "created_at": r[4]} for r in rows]
