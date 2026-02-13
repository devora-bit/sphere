"""
Sphere — Модуль задач (канбан-доска).
"""

import flet as ft
from datetime import datetime
from typing import Optional

from core.event_bus import event_bus, Events
from database import Database
from ui.components.task_item import TaskItem
from loguru import logger


class TasksModule:
    """Модуль управления задачами в стиле канбан."""

    def __init__(self, db: Database, page: ft.Page):
        self.db = db
        self.page = page

    def build(self) -> ft.Column:
        """Построить интерфейс задач."""
        # Заголовок
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.TASK_ALT, color=ft.Colors.ON_SURFACE, size=20),
                    ft.Text("Задачи", size=16, weight=ft.FontWeight.W_600),
                    ft.Container(expand=True),
                    ft.FilledButton(
                        content=ft.Text("Новая задача"),
                        icon=ft.Icons.ADD_TASK,
                        on_click=self._show_create_dialog,
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )

        # Канбан колонки
        self.todo_column = self._build_kanban_column("К выполнению", "todo", ft.Colors.BLUE_GREY)
        self.progress_column = self._build_kanban_column("В работе", "in_progress", ft.Colors.BLUE)
        self.done_column = self._build_kanban_column("Готово", "done", ft.Colors.GREEN)

        kanban = ft.Row(
            [self.todo_column, self.progress_column, self.done_column],
            expand=True,
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        )

        self._load_tasks()

        return ft.Column(
            [
                header,
                ft.Divider(height=1, thickness=0.5),
                ft.Container(
                    content=kanban,
                    expand=True,
                    padding=ft.padding.all(16),
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _build_kanban_column(self, title: str, status: str, color) -> ft.Container:
        """Построить колонку канбан-доски."""
        task_list = ft.ListView(
            expand=True,
            spacing=6,
            padding=ft.padding.all(8),
        )
        # Сохраняем ссылку на список
        setattr(self, f"_{status}_list", task_list)

        count_text = ft.Text("0", size=12, color=color, weight=ft.FontWeight.BOLD)
        setattr(self, f"_{status}_count", count_text)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(
                                    width=4, height=16, border_radius=2, bgcolor=color,
                                ),
                                ft.Text(title, size=14, weight=ft.FontWeight.W_600),
                                count_text,
                            ],
                            spacing=8,
                        ),
                        padding=ft.padding.symmetric(horizontal=8, vertical=8),
                    ),
                    task_list,
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.ON_SURFACE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE)),
        )

    def _load_tasks(self):
        """Загрузить задачи из БД."""
        for status in ["todo", "in_progress", "done"]:
            task_list = getattr(self, f"_{status}_list")
            task_list.controls.clear()
            tasks = self.db.get_tasks(status=status)
            count_text = getattr(self, f"_{status}_count")
            count_text.value = str(len(tasks))
            for task in tasks:
                item = TaskItem(
                    task=task,
                    on_status_change=self._on_status_change,
                    on_edit=self._on_edit_task,
                    on_delete=self._on_delete_task,
                )
                task_list.controls.append(item)

    def _on_status_change(self, task_id: int, new_status: str):
        """Изменить статус задачи."""
        self.db.update_task(task_id, status=new_status)
        self._load_tasks()
        self.page.update()
        event_bus.emit(Events.TASK_UPDATED, {"id": task_id, "status": new_status})
        if new_status == "done":
            event_bus.emit(Events.TASK_COMPLETED, {"id": task_id})

    def _on_edit_task(self, task_id: int):
        """Открыть диалог редактирования задачи."""
        task = None
        for t in self.db.get_tasks():
            if t["id"] == task_id:
                task = t
                break
        if not task:
            return
        self._show_task_dialog(task)

    def _on_delete_task(self, task_id: int):
        """Удалить задачу."""
        self.db.delete_task(task_id)
        self._load_tasks()
        self.page.update()
        event_bus.emit(Events.TASK_DELETED, {"id": task_id})

    def _show_create_dialog(self, e=None):
        """Показать диалог создания задачи."""
        self._show_task_dialog()

    def _show_task_dialog(self, task: dict = None):
        """Диалог создания/редактирования задачи."""
        is_edit = task is not None

        title_field = ft.TextField(
            label="Название задачи",
            value=task.get("title", "") if task else "",
            autofocus=True,
        )
        desc_field = ft.TextField(
            label="Описание",
            value=task.get("description", "") if task else "",
            multiline=True,
            min_lines=2,
            max_lines=5,
        )
        priority_dropdown = ft.Dropdown(
            label="Приоритет",
            options=[
                ft.dropdown.Option("1", "Высокий"),
                ft.dropdown.Option("2", "Средний"),
                ft.dropdown.Option("3", "Низкий"),
            ],
            value=str(task.get("priority", 2)) if task else "2",
        )
        project_field = ft.TextField(
            label="Проект",
            value=task.get("project", "") if task else "",
        )
        due_field = ft.TextField(
            label="Дедлайн (YYYY-MM-DD)",
            value=(task.get("due_date", "") or "")[:10] if task else "",
        )

        def on_save(e):
            title = title_field.value
            if not title or not title.strip():
                return
            if is_edit:
                self.db.update_task(
                    task["id"],
                    title=title.strip(),
                    description=desc_field.value or "",
                    priority=int(priority_dropdown.value or 2),
                    project=project_field.value or "",
                    due_date=due_field.value or None,
                )
            else:
                self.db.create_task(
                    title=title.strip(),
                    description=desc_field.value or "",
                    priority=int(priority_dropdown.value or 2),
                    project=project_field.value or "",
                    due_date=due_field.value or None,
                )
            self.page.pop_dialog()
            self._load_tasks()
            self.page.update()
            event_bus.emit(Events.TASK_CREATED if not is_edit else Events.TASK_UPDATED)

        dialog = ft.AlertDialog(
            title=ft.Text("Редактировать задачу" if is_edit else "Новая задача"),
            content=ft.Column(
                [title_field, desc_field, priority_dropdown, project_field, due_field],
                tight=True,
                spacing=12,
                width=400,
            ),
            actions=[
                ft.TextButton(content=ft.Text("Отмена"), on_click=lambda e: self.page.pop_dialog()),
                ft.FilledButton(content=ft.Text("Сохранить"), on_click=on_save),
            ],
        )
        self.page.show_dialog(dialog)
