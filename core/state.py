"""
Sphere — Глобальное состояние приложения.

Хранит текущее состояние и предоставляет доступ к данным.
"""

from typing import Optional, Any, Dict
from dataclasses import dataclass, field

from config import AppConfig


@dataclass
class AppState:
    """Глобальное состояние приложения."""

    # Конфигурация
    config: AppConfig = field(default_factory=AppConfig)

    # Текущий модуль
    current_module: str = "chat"

    # Состояние чата
    current_session_id: str = "default"
    is_ai_thinking: bool = False

    # Состояние заметок
    current_note_id: Optional[int] = None
    current_folder: str = "Inbox"

    # Состояние задач
    current_task_filter: str = "all"  # all, todo, in_progress, done

    # Состояние календаря
    calendar_view: str = "month"  # month, week, day, list

    # Состояние базы знаний
    current_document_id: Optional[int] = None

    # Счётчики для дашборда
    notes_count: int = 0
    tasks_todo_count: int = 0
    tasks_done_count: int = 0
    events_today_count: int = 0
    documents_count: int = 0

    # Дополнительные данные
    _data: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value

    def update_counts(self, db):
        """Обновить счётчики из базы данных."""
        try:
            conn = db.connect()
            self.notes_count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            self.tasks_todo_count = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE status = 'todo'"
            ).fetchone()[0]
            self.tasks_done_count = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE status = 'done'"
            ).fetchone()[0]
            self.events_today_count = conn.execute(
                "SELECT COUNT(*) FROM calendar_events WHERE date(start_time) = date('now')"
            ).fetchone()[0]
            self.documents_count = conn.execute(
                "SELECT COUNT(*) FROM knowledge_documents"
            ).fetchone()[0]
        except Exception:
            pass


# Глобальный экземпляр
app_state = AppState()
