"""
Sphere — Модуль заметок.
"""

import flet as ft
import json
from typing import Optional, List

from core.event_bus import event_bus, Events
from database import Database
from ui.components.note_editor import NoteEditor
from ui.themes.colors import SphereColors
from loguru import logger


class NotesModule:
    """Модуль управления заметками."""

    def __init__(self, db: Database, page: ft.Page):
        self.db = db
        self.page = page
        self.current_note_id: Optional[int] = None
        self.current_folder: str = "Все"  # совпадает с selected_index=0

    def build(self) -> ft.Row:
        """Построить интерфейс заметок."""
        # Список заметок (левая панель)
        self.notes_list = ft.ListView(
            expand=True,
            spacing=2,
            padding=ft.padding.all(8),
        )

        # Выбор папки — классические вкладки (Tabs + TabBar)
        self.folder_tabs = ft.Tabs(
            selected_index=0,
            length=6,
            on_change=self._on_folder_change,
            animation_duration=0,
            content=ft.TabBar(
                tabs=[
                    ft.Tab(label="Все"),
                    ft.Tab(label="Inbox"),
                    ft.Tab(label="Личное"),
                    ft.Tab(label="Работа"),
                    ft.Tab(label="Проекты"),
                    ft.Tab(label="Архив"),
                ]
            ),
        )

        # Кнопка создания
        create_btn = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            mini=True,
            tooltip="Новая заметка",
            on_click=self._on_create_note,
        )

        # Левая панель
        left_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.EDIT_NOTE, color=ft.Colors.ON_SURFACE, size=20),
                                ft.Text("Заметки", size=16, weight=ft.FontWeight.W_600),
                                ft.Container(expand=True),
                                create_btn,
                            ],
                            spacing=8,
                        ),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    ),
                    self.folder_tabs,
                    self.notes_list,
                ],
                spacing=0,
                expand=True,
            ),
            width=300,
            border=ft.border.only(right=ft.border.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE))),
        )

        # Редактор (правая панель)
        self.editor = NoteEditor(
            on_save=self._on_save_note,
            on_delete=self._on_delete_note,
        )

        # Плейсхолдер когда заметка не выбрана
        self.empty_state = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.EDIT_NOTE_OUTLINED, size=48, color=ft.Colors.with_opacity(0.3, ft.Colors.ON_SURFACE)),
                    ft.Text(
                        "Выберите заметку или создайте новую",
                        size=14,
                        color=ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.Alignment.CENTER,
        )

        self.right_panel = ft.Container(
            content=self.empty_state,
            expand=True,
        )

        self._load_notes()

        return ft.Row(
            [left_panel, self.right_panel],
            expand=True,
            spacing=0,
        )

    def _load_notes(self):
        """Загрузить список заметок."""
        folder = None if self.current_folder == "Все" else self.current_folder
        notes = self.db.get_notes(folder=folder)
        self.notes_list.controls.clear()

        for note in notes:
            tags = note.get("tags", "[]")
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except Exception:
                    tags = []

            pinned_icon = ft.Icon(ft.Icons.PUSH_PIN, size=12, color=ft.Colors.AMBER) if note.get("is_pinned") else None

            card = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                pinned_icon,
                                ft.Text(
                                    note["title"],
                                    size=14,
                                    weight=ft.FontWeight.W_500,
                                    expand=True,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ] if pinned_icon else [
                                ft.Text(
                                    note["title"],
                                    size=14,
                                    weight=ft.FontWeight.W_500,
                                    expand=True,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                            spacing=4,
                        ),
                        ft.Text(
                            (note.get("content", "") or "")[:60],
                            size=12,
                            color=ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE),
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Row(
                            [
                                ft.Text(
                                    note.get("folder", ""),
                                    size=10,
                                    color=ft.Colors.with_opacity(0.7, ft.Colors.ON_SURFACE),
                                ),
                                ft.Container(expand=True),
                                ft.Text(
                                    str(note.get("updated_at", ""))[:10],
                                    size=10,
                                    color=ft.Colors.with_opacity(0.4, ft.Colors.ON_SURFACE),
                                ),
                            ],
                        ),
                    ],
                    spacing=2,
                ),
                padding=ft.padding.all(10),
                border_radius=8,
                ink=True,
                on_click=lambda e, nid=note["id"]: self._on_select_note(nid),
                bgcolor=(
                    ft.Colors.with_opacity(0.15, ft.Colors.ON_SURFACE)
                    if note["id"] == self.current_note_id
                    else ft.Colors.TRANSPARENT
                ),
            )
            self.notes_list.controls.append(card)

    def _on_folder_change(self, e: ft.ControlEvent):
        """Смена активной вкладки папки."""
        folders = ["Все", "Inbox", "Личное", "Работа", "Проекты", "Архив"]
        idx = e.control.selected_index
        if 0 <= idx < len(folders):
            self.current_folder = folders[idx]
        self._load_notes()
        self.notes_list.update()

    def _on_select_note(self, note_id: int):
        """Выбрать заметку для редактирования."""
        self.current_note_id = note_id
        note = self.db.get_note(note_id)
        if note:
            self.editor.load_note(note)
            self.right_panel.content = self.editor
            self.right_panel.update()
        self._load_notes()
        self.notes_list.update()

    def _on_create_note(self, e):
        """Создать новую заметку."""
        note_id = self.db.create_note(
            title="Новая заметка",
            folder=self.current_folder if self.current_folder != "Все" else "Inbox",
        )
        self.current_note_id = note_id
        note = self.db.get_note(note_id)
        self.editor.load_note(note)
        self.right_panel.content = self.editor
        self._load_notes()
        self.page.update()
        event_bus.emit(Events.NOTE_CREATED, {"id": note_id})

    def _on_save_note(self, data: dict):
        """Сохранить заметку."""
        note_id = data.get("id")
        if note_id:
            self.db.update_note(
                note_id,
                title=data["title"],
                content=data["content"],
                folder=data["folder"],
                tags=data["tags"],
                is_pinned=data.get("is_pinned", False),
            )
            logger.info(f"Заметка #{note_id} сохранена")
            event_bus.emit(Events.NOTE_UPDATED, {"id": note_id})
        else:
            note_id = self.db.create_note(
                title=data["title"],
                content=data["content"],
                folder=data["folder"],
                tags=data["tags"],
            )
            self.editor._note_id = note_id
            logger.info(f"Заметка #{note_id} создана")
            event_bus.emit(Events.NOTE_CREATED, {"id": note_id})
        self._load_notes()
        self.page.update()

        # Показать уведомление
        self.page.show_dialog(
            ft.SnackBar(content=ft.Text("Заметка сохранена"), duration=2000)
        )

    def _on_delete_note(self, note_id: int):
        """Удалить заметку."""
        self.db.delete_note(note_id)
        self.current_note_id = None
        self.right_panel.content = self.empty_state
        self._load_notes()
        self.page.update()
        event_bus.emit(Events.NOTE_DELETED, {"id": note_id})
