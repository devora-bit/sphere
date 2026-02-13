"""
Sphere — Заголовок приложения.
"""

import flet as ft
from typing import Callable, Optional


class Header(ft.AppBar):
    """Заголовок приложения: мониторинг ресурсов, версия, поиск и действия."""

    def __init__(
        self,
        on_search: Callable = None,
        on_theme_toggle: Callable = None,
        on_sidebar_toggle: Callable = None,
        on_notifications: Callable = None,
        on_export_md: Callable = None,
        on_import_md: Callable = None,
        on_export_json: Callable = None,
        on_backup: Callable = None,
        on_about: Callable = None,
        version: str = "0.0.0.0",
        sidebar_extended: bool = True,
        **kwargs,
    ):
        self._on_search = on_search
        self._on_theme_toggle = on_theme_toggle
        self._on_sidebar_toggle = on_sidebar_toggle
        self._on_export_md = on_export_md
        self._on_import_md = on_import_md
        self._on_export_json = on_export_json
        self._on_backup = on_backup
        self._on_about = on_about

        self._cpu_text = ft.Text("CPU: —%", size=11, color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE))
        self._ram_text = ft.Text("RAM: —", size=11, color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE))
        self._monitor_row = ft.Row(
            [self._cpu_text, ft.Text("  ", size=11), self._ram_text],
            spacing=0,
            tight=True,
        )

        self.search_field = ft.TextField(
            hint_text="Спросить ИИ по вашим заметкам...",
            border_radius=20,
            height=38,
            text_size=14,
            content_padding=ft.padding.only(left=16, right=8, top=0, bottom=0),
            border_color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
            focused_border_color=ft.Colors.WHITE,
            color=ft.Colors.WHITE,
            cursor_color=ft.Colors.WHITE,
            hint_style=ft.TextStyle(color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE)),
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
            width=320,
            on_submit=self._handle_search,
            prefix_icon=ft.Icons.SEARCH,
        )

        self.theme_btn = ft.IconButton(
            icon=ft.Icons.DARK_MODE_OUTLINED,
            tooltip="Переключить тему",
            on_click=self._handle_theme_toggle,
            icon_size=20,
            icon_color=ft.Colors.WHITE,
        )

        self.sidebar_btn = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT if sidebar_extended else ft.Icons.CHEVRON_RIGHT,
            tooltip="Свернуть сайдбар" if sidebar_extended else "Развернуть сайдбар",
            on_click=self._handle_sidebar_toggle,
            icon_size=20,
            icon_color=ft.Colors.WHITE,
        )

        self.notification_btn = ft.IconButton(
            icon=ft.Icons.NOTIFICATIONS_OUTLINED,
            tooltip="Уведомления",
            on_click=on_notifications,
            icon_size=20,
            icon_color=ft.Colors.WHITE,
        )

        self.menu_btn = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            icon_color=ft.Colors.WHITE,
            items=[
                ft.PopupMenuItem(
                    icon=ft.Icons.DOWNLOAD_OUTLINED,
                    content=ft.Text("Экспорт данных (JSON)"),
                    on_click=lambda e: self._on_export_json(e) if self._on_export_json else None,
                ),
                ft.PopupMenuItem(
                    icon=ft.Icons.DESCRIPTION_OUTLINED,
                    content=ft.Text("Экспорт в Markdown (.md)"),
                    on_click=lambda e: self._on_export_md(e) if self._on_export_md else None,
                ),
                ft.PopupMenuItem(
                    icon=ft.Icons.UPLOAD_FILE_OUTLINED,
                    content=ft.Text("Импорт из папки Markdown (.md)"),
                    on_click=lambda e: self._on_import_md(e) if self._on_import_md else None,
                ),
                ft.PopupMenuItem(
                    icon=ft.Icons.BACKUP_OUTLINED,
                    content=ft.Text("Резервная копия"),
                    on_click=lambda e: self._on_backup(e) if self._on_backup else None,
                ),
                ft.PopupMenuItem(),  # разделитель
                ft.PopupMenuItem(
                    icon=ft.Icons.INFO_OUTLINED,
                    content=ft.Text("О программе Sphere"),
                    on_click=lambda e: self._on_about(e) if self._on_about else None,
                ),
            ],
        )

        super().__init__(
            leading=ft.Container(
                content=self._monitor_row,
                padding=ft.padding.only(left=14, right=20),
            ),
            leading_width=165,
            title=ft.Container(
                content=ft.Text(version, size=16, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
                margin=ft.margin.only(left=8),
            ),
            center_title=False,
            bgcolor=ft.Colors.with_opacity(0.95, "#0d1117"),
            toolbar_height=52,
            actions=[
                self.search_field,
                ft.Container(width=8),
                self.theme_btn,
                self.sidebar_btn,
                self.notification_btn,
                self.menu_btn,
            ],
            **kwargs,
        )

    def _handle_search(self, e):
        if self._on_search and e.control.value:
            self._on_search(e.control.value)
            e.control.value = ""
            e.control.update()

    def _handle_theme_toggle(self, e):
        if self._on_theme_toggle:
            self._on_theme_toggle()

    def _handle_sidebar_toggle(self, e):
        if self._on_sidebar_toggle:
            self._on_sidebar_toggle()

    def set_sidebar_extended(self, extended: bool):
        """Обновить иконку переключателя сайдбара."""
        self.sidebar_btn.icon = ft.Icons.CHEVRON_LEFT if extended else ft.Icons.CHEVRON_RIGHT
        self.sidebar_btn.tooltip = "Свернуть сайдбар" if extended else "Развернуть сайдбар"

    def set_theme_icon(self, is_dark: bool):
        """Обновить иконку темы."""
        self.theme_btn.icon = (
            ft.Icons.LIGHT_MODE_OUTLINED if is_dark else ft.Icons.DARK_MODE_OUTLINED
        )

    def update_resources(self, cpu_percent: float, ram_used_gb: float, ram_total_gb: float):
        """Обновить отображение CPU и RAM в хедере."""
        self._cpu_text.value = f"CPU: {cpu_percent:.0f}%"
        self._ram_text.value = f"RAM: {ram_used_gb:.1f}/{ram_total_gb:.1f} GB"
