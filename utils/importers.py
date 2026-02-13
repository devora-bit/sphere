"""
Sphere — Импорт данных из других форматов.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict
from loguru import logger


def import_notes_from_json(filepath: str, db) -> int:
    """Импортировать заметки из JSON файла."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        notes = data if isinstance(data, list) else data.get("notes", [])
        count = 0
        for note in notes:
            db.create_note(
                title=note.get("title", "Импортированная заметка"),
                content=note.get("content", ""),
                folder=note.get("folder", "Inbox"),
                tags=note.get("tags", []),
            )
            count += 1
        logger.info(f"Импортировано {count} заметок из {filepath}")
        return count
    except Exception as e:
        logger.error(f"Ошибка импорта: {e}")
        return 0


def import_tasks_from_csv(filepath: str, db) -> int:
    """Импортировать задачи из CSV файла."""
    try:
        count = 0
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                db.create_task(
                    title=row.get("title", row.get("name", "")),
                    description=row.get("description", ""),
                    status=row.get("status", "todo"),
                    priority=int(row.get("priority", 2)),
                    project=row.get("project", ""),
                    due_date=row.get("due_date", None),
                )
                count += 1
        logger.info(f"Импортировано {count} задач из {filepath}")
        return count
    except Exception as e:
        logger.error(f"Ошибка импорта CSV: {e}")
        return 0


def import_markdown_files(directory: str, db) -> int:
    """Импортировать все .md файлы из директории."""
    try:
        dir_path = Path(directory)
        count = 0
        for md_file in dir_path.glob("**/*.md"):
            title = md_file.stem
            content = md_file.read_text(encoding="utf-8")
            db.create_note(
                title=title,
                content=content,
                folder="Импорт",
            )
            count += 1
        logger.info(f"Импортировано {count} Markdown файлов из {directory}")
        return count
    except Exception as e:
        logger.error(f"Ошибка импорта MD: {e}")
        return 0
