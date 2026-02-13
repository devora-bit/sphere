"""
Sphere — Компонент элемента задачи.
"""

import flet as ft
from typing import Callable, Optional
from ui.themes.colors import SphereColors


PRIORITY_LABELS = {1: "Высокий", 2: "Средний", 3: "Низкий"}
PRIORITY_COLORS = {
    1: SphereColors.PRIORITY_HIGH,
    2: SphereColors.PRIORITY_MEDIUM,
    3: SphereColors.PRIORITY_LOW,
}
STATUS_LABELS = {"todo": "К выполнению", "in_progress": "В работе", "done": "Готово"}
STATUS_COLORS = {
    "todo": SphereColors.STATUS_TODO,
    "in_progress": SphereColors.STATUS_IN_PROGRESS,
    "done": SphereColors.STATUS_DONE,
}


class TaskItem(ft.Container):
    """Карточка задачи для канбан-доски или списка."""

    def __init__(
        self,
        task: dict,
        on_status_change: Callable = None,
        on_edit: Callable = None,
        on_delete: Callable = None,
        **kwargs,
    ):
        self.task = task
        self._on_status_change = on_status_change
        self._on_edit = on_edit
        self._on_delete = on_delete

        task_id = task.get("id", 0)
        title = task.get("title", "")
        description = task.get("description", "")
        status = task.get("status", "todo")
        priority = task.get("priority", 2)
        due_date = task.get("due_date", "")
        project = task.get("project", "")

        # Чекбокс
        checkbox = ft.Checkbox(
            value=status == "done",
            on_change=lambda e: self._handle_toggle(e, task_id),
        )

        # Заголовок задачи
        title_text = ft.Text(
            title,
            size=14,
            weight=ft.FontWeight.W_500,
            text_decoration=(
                ft.TextDecoration.LINE_THROUGH if status == "done" else None
            ),
            color=(
                ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE) if status == "done" else None
            ),
            expand=True,
        )

        # Приоритет
        priority_chip = ft.Container(
            content=ft.Text(
                PRIORITY_LABELS.get(priority, ""),
                size=10,
                color=ft.Colors.WHITE,
            ),
            bgcolor=PRIORITY_COLORS.get(priority, ft.Colors.GREY),
            border_radius=4,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
        )

        # Дедлайн
        due_text = ft.Text(
            due_date[:10] if due_date else "",
            size=11,
            color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
            visible=bool(due_date),
        )

        # Проект
        project_text = ft.Text(
            project,
            size=11,
            color=ft.Colors.with_opacity(0.7, ft.Colors.ON_SURFACE),
            visible=bool(project),
        )

        # Описание
        desc_text = ft.Text(
            description[:80] + "..." if len(description) > 80 else description,
            size=12,
            color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
            visible=bool(description),
        )

        # Меню действий
        menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_HORIZ,
            icon_size=16,
            items=[
                ft.PopupMenuItem(
                    icon=ft.Icons.EDIT_OUTLINED,
                    content=ft.Text("Редактировать"),
                    on_click=lambda e: self._handle_edit(task_id),
                ),
                ft.PopupMenuItem(
                    icon=ft.Icons.ARROW_FORWARD,
                    content=ft.Text("В работу" if status == "todo" else "Готово"),
                    on_click=lambda e: self._handle_next_status(task_id, status),
                ),
                ft.PopupMenuItem(),
                ft.PopupMenuItem(
                    icon=ft.Icons.DELETE_OUTLINED,
                    content=ft.Text("Удалить"),
                    on_click=lambda e: self._handle_delete(task_id),
                ),
            ],
        )

        super().__init__(
            content=ft.Column(
                [
                    ft.Row(
                        [checkbox, title_text, priority_chip, menu],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                    ),
                    desc_text,
                    ft.Row(
                        [project_text, ft.Container(expand=True), due_text],
                        visible=bool(project or due_date),
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.all(12),
            border_radius=8,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)),
            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE),
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            on_hover=self._on_hover,
            **kwargs,
        )

    def _on_hover(self, e):
        self.bgcolor = (
            ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE)
            if e.data == "true"
            else ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE)
        )
        self.update()

    def _handle_toggle(self, e, task_id):
        new_status = "done" if e.control.value else "todo"
        if self._on_status_change:
            self._on_status_change(task_id, new_status)

    def _handle_next_status(self, task_id, current):
        next_map = {"todo": "in_progress", "in_progress": "done", "done": "todo"}
        if self._on_status_change:
            self._on_status_change(task_id, next_map.get(current, "todo"))

    def _handle_edit(self, task_id):
        if self._on_edit:
            self._on_edit(task_id)

    def _handle_delete(self, task_id):
        if self._on_delete:
            self._on_delete(task_id)
