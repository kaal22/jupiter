"""Jupiter memory store — session, episodic, preferences (SQLite)."""
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional
from jupiter.config import DB_PATH, ensure_dirs


class MemoryStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or DB_PATH
        ensure_dirs()
        self._init_schema()

    def _conn(self):
        return sqlite3.connect(self.path)

    def _init_schema(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS session (
                    id INTEGER PRIMARY KEY, role TEXT NOT NULL, content TEXT NOT NULL, created_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS episodic (
                    id INTEGER PRIMARY KEY, summary TEXT NOT NULL, metadata TEXT, created_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at REAL NOT NULL);
            """)

    def session_append(self, role: str, content: str):
        with self._conn() as c:
            c.execute("INSERT INTO session (role, content, created_at) VALUES (?, ?, ?)", (role, content, time.time()))

    def session_get_recent(self, limit: int = 50):
        with self._conn() as c:
            rows = c.execute("SELECT role, content, created_at FROM session ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"role": r[0], "content": r[1], "created_at": r[2]} for r in reversed(rows)]

    def session_clear(self):
        with self._conn() as c:
            c.execute("DELETE FROM session")

    def episodic_add(self, summary: str, metadata: Optional[dict] = None):
        with self._conn() as c:
            c.execute("INSERT INTO episodic (summary, metadata, created_at) VALUES (?, ?, ?)", (summary, json.dumps(metadata or {}), time.time()))

    def episodic_get_recent(self, limit: int = 20):
        with self._conn() as c:
            rows = c.execute("SELECT summary, metadata, created_at FROM episodic ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"summary": r[0], "metadata": json.loads(r[1] or "{}"), "created_at": r[2]} for r in rows]

    def preference_set(self, key: str, value: Any):
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, ?)", (key, json.dumps(value), time.time()))

    def preference_get(self, key: str, default: Any = None):
        with self._conn() as c:
            row = c.execute("SELECT value FROM preferences WHERE key = ?", (key,)).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return row[0]

    def get_context_for_agent(self, session_limit: int = 30, episodic_limit: int = 10):
        parts = []
        prefs = {}
        for key in ("model", "editor", "theme", "speed_quality"):
            v = self.preference_get(key)
            if v is not None:
                prefs[key] = v
        if prefs:
            parts.append("User preferences: " + json.dumps(prefs))
        for e in self.episodic_get_recent(episodic_limit):
            parts.append("Past: " + e["summary"])
        for m in self.session_get_recent(session_limit):
            parts.append(f"{m['role']}: {m['content']}")
        return "\n".join(parts) if parts else ""
