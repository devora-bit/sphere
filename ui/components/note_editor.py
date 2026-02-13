"""
Sphere — Компонент редактора заметок с Markdown.
"""

import flet as ft
from typing import Callable, Optional


class NoteEditor(ft.Column):
    """Редактор заметки с поддержкой Markdown и live-предпросмотром."""

    def __init__(
        self,
        on_save: Callable = None,
        on_delete: Callable = None,
        **kwargs,
    ):
        self._on_save = on_save
        self._on_delete = on_delete
        self._note_id: Optional[int] = None
        self._show_preview = False
        self._is_pinned: bool = False

        # Поле заголовка
        self.title_field = ft.TextField(
            hint_text="Заголовок заметки",
            border=ft.InputBorder.NONE,
            text_size=22,
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            content_padding=ft.padding.only(left=16, right=16, bottom=8),
        )

        # Поле тегов
        self.tags_field = ft.TextField(
            hint_text="Теги (через запятую)",
            border=ft.InputBorder.UNDERLINE,
            text_size=13,
            prefix_icon=ft.Icons.TAG,
            content_padding=ft.padding.only(left=8, right=16),
            height=36,
        )

        # Поле папки
        self.folder_dropdown = ft.Dropdown(
            hint_text="Папка",
            width=180,
            height=36,
            text_size=13,
            options=[
                ft.dropdown.Option("Inbox"),
                ft.dropdown.Option("Личное"),
                ft.dropdown.Option("Работа"),
                ft.dropdown.Option("Проекты"),
                ft.dropdown.Option("Архив"),
            ],
            value="Inbox",
        )

        # Область редактирования
        self.content_field = ft.TextField(
            hint_text="Начните писать... (поддерживается Markdown)",
            multiline=True,
            min_lines=15,
            max_lines=None,
            expand=True,
            border=ft.InputBorder.NONE,
            text_size=14,
            content_padding=ft.padding.all(16),
            on_change=self._on_content_change,
        )

        # Область предпросмотра Markdown
        self.preview_area = ft.Container(
            content=ft.Markdown(
                "",
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            ),
            padding=ft.padding.all(16),
            visible=False,
            expand=True,
        )

        # Панель инструментов
        self.pin_button = ft.IconButton(
            icon=ft.Icons.PUSH_PIN_OUTLINED,
            tooltip="Закрепить",
            icon_size=18,
            on_click=self._toggle_pin,
        )

        toolbar = ft.Row(
            [
                self.folder_dropdown,
                ft.Container(width=8),
                self.tags_field,
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.PREVIEW_OUTLINED,
                    tooltip="Предпросмотр Markdown",
                    on_click=self._toggle_preview,
                    icon_size=18,
                ),
                self.pin_button,
                ft.FilledButton(
                    content=ft.Text("Сохранить"),
                    icon=ft.Icons.SAVE_OUTLINED,
                    on_click=self._handle_save,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    tooltip="Удалить",
                    on_click=self._handle_delete,
                    icon_size=18,
                    icon_color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        )

        # Область контента (редактор + предпросмотр)
        self.content_area = ft.Row(
            [
                ft.Container(content=self.content_field, expand=True),
                self.preview_area,
            ],
            expand=True,
            spacing=0,
        )

        super().__init__(
            controls=[
                self.title_field,
                ft.Divider(height=1, thickness=0.5),
                ft.Container(content=toolbar, padding=ft.padding.symmetric(horizontal=8, vertical=4)),
                ft.Divider(height=1, thickness=0.5),
                self.content_area,
            ],
            spacing=0,
            expand=True,
            **kwargs,
        )

    def load_note(self, note: dict):
        """Загрузить заметку в редактор."""
        self._note_id = note.get("id")
        self.title_field.value = note.get("title", "")
        self.content_field.value = note.get("content", "")
        self.folder_dropdown.value = note.get("folder", "Inbox")
         # pinned
        self._is_pinned = bool(note.get("is_pinned", 0))
        self.pin_button.icon = (
            ft.Icons.PUSH_PIN if self._is_pinned else ft.Icons.PUSH_PIN_OUTLINED
        )
        tags = note.get("tags", "[]")
        if isinstance(tags, str):
            import json
            try:
                tags = json.loads(tags)
            except Exception:
                tags = []
        self.tags_field.value = ", ".join(tags) if isinstance(tags, list) else str(tags)

    def clear(self):
        """Очистить редактор."""
        self._note_id = None
        self.title_field.value = ""
        self.content_field.value = ""
        self.tags_field.value = ""
        self.folder_dropdown.value = "Inbox"
        self._is_pinned = False
        self.pin_button.icon = ft.Icons.PUSH_PIN_OUTLINED

    def get_data(self) -> dict:
        """Получить данные из редактора."""
        tags_raw = self.tags_field.value or ""
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        return {
            "id": self._note_id,
            "title": self.title_field.value or "Без заголовка",
            "content": self.content_field.value or "",
            "folder": self.folder_dropdown.value or "Inbox",
            "tags": tags,
            "is_pinned": self._is_pinned,
        }

    def _toggle_preview(self, e):
        self._show_preview = not self._show_preview
        self.preview_area.visible = self._show_preview
        if self._show_preview:
            md = self.preview_area.content
            md.value = self.content_field.value or "*Пустая заметка*"
        self.update()

    def _on_content_change(self, e):
        if self._show_preview:
            md = self.preview_area.content
            md.value = self.content_field.value or "*Пустая заметка*"
            self.preview_area.update()

    def _toggle_pin(self, e):
        """Переключить флаг закрепления заметки."""
        self._is_pinned = not self._is_pinned
        self.pin_button.icon = (
            ft.Icons.PUSH_PIN if self._is_pinned else ft.Icons.PUSH_PIN_OUTLINED
        )
        self.pin_button.update()

    def _handle_save(self, e):
        if self._on_save:
            self._on_save(self.get_data())

    def _handle_delete(self, e):
        if self._on_delete and self._note_id:
            self._on_delete(self._note_id)
