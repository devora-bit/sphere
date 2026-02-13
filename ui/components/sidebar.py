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

    def __init__(self, on_module_change: Callable = None, on_toggle_compact: Callable = None, extended: bool = True, **kwargs):
        self._on_module_change = on_module_change
        self._on_toggle_compact = on_toggle_compact
        self._extended = extended

        destinations = [
            ft.NavigationRailDestination(
                icon=icon,
                selected_icon=selected_icon,
                label=label,
                padding=ft.padding.symmetric(vertical=4),
            )
            for _, icon, selected_icon, label in self.MODULE_ICONS
        ]

        self._collapse_btn = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT if extended else ft.Icons.CHEVRON_RIGHT,
            icon_size=20,
            icon_color=ft.Colors.WHITE,
            tooltip="Свернуть сайдбар" if extended else "Развернуть сайдбар",
            on_click=self._on_collapse_click,
        )

        if extended:
            leading_content = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.BLUR_CIRCULAR, color=ft.Colors.WHITE, size=24),
                            ft.Text("Sphere", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    ft.Divider(height=1, thickness=0.5, color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
                    self._collapse_btn,
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            leading_padding = ft.padding.only(top=12, bottom=8, left=12, right=12)
        else:
            leading_content = ft.Column(
                [
                    ft.Icon(ft.Icons.BLUR_CIRCULAR, color=ft.Colors.WHITE, size=22),
                    ft.Divider(height=8, thickness=0),
                    self._collapse_btn,
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            leading_padding = ft.padding.only(top=12, bottom=8, left=8, right=8)

        super().__init__(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL if extended else ft.NavigationRailLabelType.NONE,
            min_width=72,
            min_extended_width=220 if extended else 72,
            extended=extended,
            group_alignment=-0.9,
            leading=ft.Container(content=leading_content, padding=leading_padding),
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

    def _on_collapse_click(self, e):
        if self._on_toggle_compact:
            self._on_toggle_compact()

    def select_module(self, module_key: str):
        """Выбрать модуль программно."""
        for i, (key, *_) in enumerate(self.MODULE_ICONS):
            if key == module_key:
                self.selected_index = i
                break

    def set_compact(self, compact: bool):
        """Переключить компактный режим (только иконки)."""
        self._extended = not compact
        self.extended = not compact
        self.label_type = ft.NavigationRailLabelType.NONE if compact else ft.NavigationRailLabelType.ALL
        self.min_extended_width = 72 if compact else 220
        self._collapse_btn.icon = ft.Icons.CHEVRON_RIGHT if compact else ft.Icons.CHEVRON_LEFT
        self._collapse_btn.tooltip = "Развернуть сайдбар" if compact else "Свернуть сайдбар"
