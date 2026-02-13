"""
Sphere — Главная панель (дашборд).
"""

import flet as ft
from typing import Callable

from ui.themes.colors import SphereColors


class DashboardLayout(ft.Column):
    """Главный дашборд с обзором всех модулей."""

    def __init__(self, state=None, on_navigate: Callable = None, **kwargs):
        self._state = state
        self._on_navigate = on_navigate

        # Приветствие
        greeting = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Добро пожаловать в Sphere",
                        size=26,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "Ваш персональный AI-ассистент для продуктивности",
                        size=14,
                        color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.only(left=24, top=24, bottom=16),
        )

        # Статистические карточки
        stats = state or type("S", (), {
            "notes_count": 0, "tasks_todo_count": 0,
            "tasks_done_count": 0, "events_today_count": 0, "documents_count": 0
        })()

        stats_row = ft.Row(
            [
                self._stat_card("Заметки", str(stats.notes_count), ft.Icons.EDIT_NOTE, ft.Colors.ON_SURFACE, "notes"),
                self._stat_card("Задачи", str(stats.tasks_todo_count), ft.Icons.TASK_ALT, ft.Colors.ON_SURFACE, "tasks"),
                self._stat_card("Выполнено", str(stats.tasks_done_count), ft.Icons.CHECK_CIRCLE, ft.Colors.ON_SURFACE, "tasks"),
                self._stat_card("Сегодня", str(stats.events_today_count), ft.Icons.CALENDAR_TODAY, ft.Colors.ON_SURFACE, "calendar"),
                self._stat_card("Документы", str(stats.documents_count), ft.Icons.SCHOOL, ft.Colors.ON_SURFACE, "knowledge"),
            ],
            wrap=True,
            spacing=12,
            run_spacing=12,
        )

        # Быстрые действия
        quick_actions = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Быстрые действия", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                    ft.Row(
                        [
                            ft.FilledButton(
                                content=ft.Text("Новый чат"),
                                icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
                                on_click=lambda e: self._navigate("chat"),
                            ),
                            ft.FilledButton(
                                content=ft.Text("Новая заметка"),
                                icon=ft.Icons.ADD_OUTLINED,
                                on_click=lambda e: self._navigate("notes"),
                            ),
                            ft.FilledButton(
                                content=ft.Text("Новая задача"),
                                icon=ft.Icons.ADD_TASK,
                                on_click=lambda e: self._navigate("tasks"),
                            ),
                            ft.FilledButton(
                                content=ft.Text("Спросить ИИ"),
                                icon=ft.Icons.AUTO_AWESOME,
                                on_click=lambda e: self._navigate("chat"),
                            ),
                        ],
                        wrap=True,
                        spacing=8,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
        )

        # AI подсказка
        ai_tip = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.ON_SURFACE),
                    ft.Column(
                        [
                            ft.Text("Совет от Sphere AI", size=14, weight=ft.FontWeight.W_600),
                            ft.Text(
                                "Попробуйте задать вопрос в чате, например: «Какие задачи у меня на сегодня?» "
                                "или «Составь план на неделю»",
                                size=13,
                                color=ft.Colors.with_opacity(0.7, ft.Colors.ON_SURFACE),
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.padding.all(16),
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
            margin=ft.margin.symmetric(horizontal=24),
        )

        super().__init__(
            controls=[
                greeting,
                ft.Container(content=stats_row, padding=ft.padding.symmetric(horizontal=24)),
                ft.Divider(height=24, thickness=0),
                quick_actions,
                ft.Divider(height=16, thickness=0),
                ai_tip,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            **kwargs,
        )

    def _stat_card(self, label: str, value: str, icon, color, module: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [ft.Icon(icon, color=color, size=22)],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    ft.Text(value, size=28, weight=ft.FontWeight.BOLD),
                    ft.Text(label, size=13, color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE)),
                ],
                spacing=4,
            ),
            width=160,
            height=110,
            padding=ft.padding.all(16),
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.ON_SURFACE)),
            on_click=lambda e: self._navigate(module),
            ink=True,
        )

    def _navigate(self, module: str):
        if self._on_navigate:
            self._on_navigate(module)
