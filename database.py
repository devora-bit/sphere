"""
Sphere — Инициализация и управление SQLite базой данных.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from config import DB_PATH, DATA_DIR
from loguru import logger


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    settings JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    folder TEXT DEFAULT 'Inbox',
    tags JSON DEFAULT '[]',
    is_pinned BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vector_id TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'todo',
    priority INTEGER DEFAULT 2,
    due_date TIMESTAMP,
    project TEXT DEFAULT '',
    parent_task_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    location TEXT,
    is_all_day BOOLEAN DEFAULT 0,
    color TEXT DEFAULT '',
    external_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    filetype TEXT,
    title TEXT,
    summary TEXT,
    tags JSON DEFAULT '[]',
    processed BOOLEAN DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT DEFAULT 'default',
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    context JSON DEFAULT '{}',
    provider TEXT DEFAULT 'ollama',
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    results JSON DEFAULT '[]',
    module TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    category TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_notes_folder ON notes(folder);
CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_calendar_start ON calendar_events(start_time);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id, created_at);
"""


class Database:
    """Менеджер SQLite базы данных."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Подключиться к базе данных."""
        if self._conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            logger.info(f"Подключение к БД: {self.db_path}")
        return self._conn

    def initialize(self):
        """Инициализировать схему базы данных."""
        conn = self.connect()
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        logger.info("Схема БД инициализирована")

    def close(self):
        """Закрыть подключение."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # --- Заметки ---
    def get_notes(self, folder: Optional[str] = None, limit: int = 100) -> List[Dict]:
        conn = self.connect()
        if folder:
            rows = conn.execute(
                "SELECT * FROM notes WHERE folder = ? ORDER BY is_pinned DESC, updated_at DESC LIMIT ?",
                (folder, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM notes ORDER BY is_pinned DESC, updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_note(self, note_id: int) -> Optional[Dict]:
        conn = self.connect()
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        return dict(row) if row else None

    def create_note(self, title: str, content: str = "", folder: str = "Inbox", tags: list = None) -> int:
        conn = self.connect()
        cur = conn.execute(
            "INSERT INTO notes (title, content, folder, tags) VALUES (?, ?, ?, ?)",
            (title, content, folder, json.dumps(tags or [])),
        )
        conn.commit()
        return cur.lastrowid

    def update_note(self, note_id: int, **kwargs):
        conn = self.connect()
        allowed = {"title", "content", "folder", "tags", "is_pinned", "vector_id"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if "tags" in fields and isinstance(fields["tags"], list):
            fields["tags"] = json.dumps(fields["tags"])
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [note_id]
        conn.execute(f"UPDATE notes SET {set_clause} WHERE id = ?", values)
        conn.commit()

    def delete_note(self, note_id: int):
        conn = self.connect()
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()

    # --- Задачи ---
    def get_tasks(self, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        conn = self.connect()
        if status:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY priority ASC, due_date ASC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY status, priority ASC, due_date ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def create_task(self, title: str, description: str = "", status: str = "todo",
                    priority: int = 2, due_date: str = None, project: str = "") -> int:
        conn = self.connect()
        cur = conn.execute(
            "INSERT INTO tasks (title, description, status, priority, due_date, project) VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, status, priority, due_date, project),
        )
        conn.commit()
        return cur.lastrowid

    def update_task(self, task_id: int, **kwargs):
        conn = self.connect()
        allowed = {"title", "description", "status", "priority", "due_date", "project", "parent_task_id"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [task_id]
        conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        conn.commit()

    def delete_task(self, task_id: int):
        conn = self.connect()
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

    # --- Календарные события ---
    def get_events(self, start_from: str = None, start_to: str = None, limit: int = 100) -> List[Dict]:
        conn = self.connect()
        query = "SELECT * FROM calendar_events"
        params = []
        conditions = []
        if start_from:
            conditions.append("start_time >= ?")
            params.append(start_from)
        if start_to:
            conditions.append("start_time <= ?")
            params.append(start_to)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY start_time ASC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def create_event(self, title: str, start_time: str, end_time: str = None,
                     description: str = "", location: str = "", is_all_day: bool = False, color: str = "") -> int:
        conn = self.connect()
        cur = conn.execute(
            "INSERT INTO calendar_events (title, start_time, end_time, description, location, is_all_day, color) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, start_time, end_time, description, location, is_all_day, color),
        )
        conn.commit()
        return cur.lastrowid

    def update_event(self, event_id: int, **kwargs):
        conn = self.connect()
        allowed = {"title", "description", "start_time", "end_time", "location", "is_all_day", "color"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [event_id]
        conn.execute(f"UPDATE calendar_events SET {set_clause} WHERE id = ?", values)
        conn.commit()

    def delete_event(self, event_id: int):
        conn = self.connect()
        conn.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
        conn.commit()

    # --- История чата ---
    def add_chat_message(self, role: str, content: str, session_id: str = "default",
                         provider: str = "ollama", context: dict = None, tokens: int = 0):
        conn = self.connect()
        conn.execute(
            "INSERT INTO chat_history (session_id, role, content, provider, context, tokens_used) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, role, content, provider, json.dumps(context or {}), tokens),
        )
        conn.commit()

    def get_chat_history(self, session_id: str = "default", limit: int = 50) -> List[Dict]:
        conn = self.connect()
        rows = conn.execute(
            "SELECT * FROM chat_history WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_chat_sessions(self) -> List[str]:
        conn = self.connect()
        rows = conn.execute(
            "SELECT session_id FROM chat_history GROUP BY session_id ORDER BY MAX(created_at) DESC"
        ).fetchall()
        return [r["session_id"] for r in rows]

    # --- База знаний ---
    def add_document(self, filename: str, filepath: str, filetype: str, title: str = "") -> int:
        conn = self.connect()
        cur = conn.execute(
            "INSERT INTO knowledge_documents (filename, filepath, filetype, title) VALUES (?, ?, ?, ?)",
            (filename, filepath, filetype, title or filename),
        )
        conn.commit()
        return cur.lastrowid

    def get_documents(self, limit: int = 100) -> List[Dict]:
        conn = self.connect()
        rows = conn.execute(
            "SELECT * FROM knowledge_documents ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def update_document(self, doc_id: int, **kwargs):
        conn = self.connect()
        allowed = {"title", "summary", "tags", "processed", "chunk_count"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if "tags" in fields and isinstance(fields["tags"], list):
            fields["tags"] = json.dumps(fields["tags"])
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [doc_id]
        conn.execute(f"UPDATE knowledge_documents SET {set_clause} WHERE id = ?", values)
        conn.commit()

    # --- Настройки ---
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        conn = self.connect()
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str, category: str = "general"):
        conn = self.connect()
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, category, updated_at) VALUES (?, ?, ?, ?)",
            (key, value, category, datetime.now().isoformat()),
        )
        conn.commit()

    # --- Поиск ---
    def search_notes(self, query: str) -> List[Dict]:
        conn = self.connect()
        rows = conn.execute(
            "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY updated_at DESC LIMIT 20",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
        return [dict(r) for r in rows]

    def search_tasks(self, query: str) -> List[Dict]:
        conn = self.connect()
        rows = conn.execute(
            "SELECT * FROM tasks WHERE title LIKE ? OR description LIKE ? ORDER BY updated_at DESC LIMIT 20",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
        return [dict(r) for r in rows]


# Глобальный экземпляр
db = Database()
