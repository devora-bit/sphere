"""
Sphere — Боковая панель навигации.
"""

import flet as ft
from typing import Callable, Optional


class Sidebar(ft.NavigationRail):
    """Боковая панель навигации Sphere."""

    MODULE_ICONS = [
        ("chat", ft.Icons.CHAT_BUBBLE_OUTLINE, ft.Icons.CHAT_BUBBLE, "Чат с ИИ"),
        ("notes", ft.Icons.EDIT_NOTE_OUTLINED, ft.Icons.EDIT_NOTE, "Заметки"),
        ("tasks", ft.Icons.TASK_ALT_OUTLINED, ft.Icons.TASK_ALT, "Задачи"),
        ("calendar", ft.Icons.CALENDAR_TODAY_OUTLINED, ft.Icons.CALENDAR_TODAY, "Календарь"),
        ("knowledge", ft.Icons.SCHOOL_OUTLINED, ft.Icons.SCHOOL, "База знаний"),
        ("settings", ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS, "Настройки"),
        ("profile", ft.Icons.PERSON_OUTLINE, ft.Icons.PERSON, "Личный кабинет"),
        ("about", ft.Icons.INFO_OUTLINE, ft.Icons.INFO, "О проекте"),
    ]

    def __init__(self, on_module_change: Callable = None, **kwargs):
        self._on_module_change = on_module_change

        destinations = [
            ft.NavigationRailDestination(
                icon=icon,
                selected_icon=selected_icon,
                label=label,
                padding=ft.padding.symmetric(vertical=4),
            )
            for _, icon, selected_icon, label in self.MODULE_ICONS
        ]

        super().__init__(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=80,
            min_extended_width=220,
            extended=True,
            group_alignment=-0.9,
            leading=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.BLUR_CIRCULAR, color=ft.Colors.WHITE, size=28),
                                ft.Text(
                                    "Sphere",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        ft.Divider(height=1, thickness=0.5, color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
                    ],
                    spacing=12,
                ),
                padding=ft.padding.only(top=12, bottom=8, left=16, right=16),
            ),
            destinations=destinations,
            on_change=self._handle_change,
            bgcolor=ft.Colors.PRIMARY,
            indicator_color=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
            unselected_label_text_style=ft.TextStyle(color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE)),
            selected_label_text_style=ft.TextStyle(color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
            **kwargs,
        )

    def _handle_change(self, e):
        if self._on_module_change:
            module_key = self.MODULE_ICONS[e.control.selected_index][0]
            self._on_module_change(module_key)

    def select_module(self, module_key: str):
        """Выбрать модуль программно."""
        for i, (key, *_) in enumerate(self.MODULE_ICONS):
            if key == module_key:
                self.selected_index = i
                break
