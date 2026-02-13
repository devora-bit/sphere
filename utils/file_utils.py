"""
Sphere — Утилиты для работы с файлами.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import DATA_DIR, BACKUPS_DIR, NOTES_DIR, EXPORTS_DIR
from loguru import logger


def ensure_dir(path: Path):
    """Создать директорию если не существует."""
    path.mkdir(parents=True, exist_ok=True)


def get_file_size_str(size_bytes: int) -> str:
    """Человекочитаемый размер файла."""
    for unit in ["Б", "КБ", "МБ", "ГБ"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} ТБ"


def create_backup(db_path: Path) -> Optional[str]:
    """Создать резервную копию базы данных."""
    try:
        ensure_dir(BACKUPS_DIR)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"sphere_backup_{timestamp}.db"
        backup_path = BACKUPS_DIR / backup_name
        shutil.copy2(db_path, backup_path)
        logger.info(f"Бэкап создан: {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"Ошибка создания бэкапа: {e}")
        return None


def export_notes_to_files(db) -> str:
    """Экспортировать все заметки в Markdown файлы."""
    ensure_dir(EXPORTS_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = EXPORTS_DIR / f"notes_{timestamp}"
    export_dir.mkdir(parents=True, exist_ok=True)

    notes = db.get_notes(limit=10000)
    for note in notes:
        title = note.get("title", "untitled").replace("/", "_").replace("\\", "_")
        content = note.get("content", "")
        filename = f"{title}.md"
        with open(export_dir / filename, "w", encoding="utf-8") as f:
            f.write(f"# {note.get('title', '')}\n\n")
            f.write(content)

    logger.info(f"Экспортировано {len(notes)} заметок в {export_dir}")
    return str(export_dir)


def export_data_to_json(db) -> str:
    """Экспортировать все данные в JSON."""
    ensure_dir(EXPORTS_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = EXPORTS_DIR / f"sphere_export_{timestamp}.json"

    data = {
        "notes": db.get_notes(limit=10000),
        "tasks": db.get_tasks(limit=10000),
        "events": db.get_events(limit=10000),
        "documents": db.get_documents(limit=10000),
        "exported_at": datetime.now().isoformat(),
    }

    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"Данные экспортированы: {export_path}")
    return str(export_path)


def list_backups() -> list:
    """Получить список бэкапов."""
    if not BACKUPS_DIR.exists():
        return []
    backups = []
    for f in sorted(BACKUPS_DIR.glob("sphere_backup_*.db"), reverse=True):
        backups.append({
            "filename": f.name,
            "path": str(f),
            "size": get_file_size_str(f.stat().st_size),
            "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        })
    return backups


def restore_from_export(db, export_path) -> None:
    """
    Восстановить данные из JSON-экспорта (заметки, задачи, события, документы).
    Записи добавляются к существующим, id из файла не используются.
    """
    path = Path(export_path)
    if not path.exists():
        raise FileNotFoundError(export_path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    notes = data.get("notes", [])
    tasks = data.get("tasks", [])
    events = data.get("events", [])
    documents = data.get("documents", [])

    for n in notes:
        tags = n.get("tags")
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except Exception:
                tags = []
        db.create_note(
            title=n.get("title", ""),
            content=n.get("content", ""),
            folder=n.get("folder", "Inbox"),
            tags=tags or [],
        )
    logger.info(f"Восстановлено заметок: {len(notes)}")

    for t in tasks:
        db.create_task(
            title=t.get("title", ""),
            description=t.get("description", ""),
            status=t.get("status", "todo"),
            priority=int(t.get("priority", 2)),
            due_date=t.get("due_date"),
            project=t.get("project", ""),
        )
    logger.info(f"Восстановлено задач: {len(tasks)}")

    for ev in events:
        db.create_event(
            title=ev.get("title", ""),
            start_time=ev.get("start_time", ""),
            end_time=ev.get("end_time"),
            description=ev.get("description", ""),
            location=ev.get("location", ""),
            is_all_day=bool(ev.get("is_all_day", False)),
            color=ev.get("color", ""),
        )
    logger.info(f"Восстановлено событий: {len(events)}")

    for d in documents:
        db.add_document(
            filename=d.get("filename", ""),
            filepath=d.get("filepath", ""),
            filetype=d.get("filetype", ""),
            title=d.get("title", ""),
        )
    logger.info(f"Восстановлено документов (метаданные): {len(documents)}")
