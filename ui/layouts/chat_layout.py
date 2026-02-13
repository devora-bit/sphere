"""
Sphere — Макет чата с ИИ.
"""

import flet as ft
import asyncio
from typing import Callable, Optional
from datetime import datetime

from ui.components.chat_message import ChatMessage, TypingIndicator, clear_handlers


class ChatLayout(ft.Column):
    """Полный макет страницы чата с ИИ."""

    def __init__(
        self,
        page=None,
        on_send: Callable = None,
        on_new_session: Callable = None,
        on_session_select: Callable = None,
        ai_mode: str = "hybrid",
        on_ai_mode_change: Callable = None,
        agent_name: str = None,
        **kwargs,
    ):
        self._page = page
        self._on_send = on_send
        self._on_new_session = on_new_session
        self._on_session_select = on_session_select
        self._on_ai_mode_change = on_ai_mode_change
        self._agent_name = (agent_name or "").strip() or "Sphere AI"

        # Режим общения с ИИ
        self.mode_dropdown = ft.Dropdown(
            width=260,
            height=36,
            text_size=13,
            value=ai_mode if ai_mode in ("knowledge", "hybrid", "model_only") else "hybrid",
            options=[
                ft.dropdown.Option("knowledge", "Только база знаний"),
                ft.dropdown.Option("hybrid", "Гибрид (знания + модель)"),
                ft.dropdown.Option("model_only", "Только модель"),
            ],
            on_select=lambda e: (self._on_ai_mode_change(e.control.value) if e.control.value else None) if self._on_ai_mode_change else None,
        )

        # Список сообщений
        self.messages_list = ft.ListView(
            expand=True,
            spacing=2,
            auto_scroll=True,
            padding=ft.padding.only(top=8, bottom=8),
        )

        # Индикатор загрузки
        self.typing_indicator = TypingIndicator(visible=False)

        # Поле ввода сообщения
        self.message_input = ft.TextField(
            hint_text="Спросите у ИИ или дайте команду...",
            multiline=True,
            shift_enter=True,
            min_lines=1,
            max_lines=5,
            expand=True,
            border_radius=20,
            filled=True,
            content_padding=ft.padding.only(left=20, right=8, top=10, bottom=10),
            text_size=14,
            on_submit=self._handle_send,
        )

        # Кнопка отправки
        send_btn = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            tooltip="Отправить",
            on_click=self._handle_send,
            icon_color=ft.Colors.ON_SURFACE,
            icon_size=22,
        )

        # Панель сессий
        self.sessions_dropdown = ft.Dropdown(
            hint_text="Сессия",
            width=180,
            height=36,
            text_size=13,
            options=[ft.dropdown.Option("default", "Новый чат")],
            value="default",
            on_select=self._handle_session_change,
        )

        # Верхняя панель чата
        chat_header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CHAT_BUBBLE, color=ft.Colors.ON_SURFACE, size=20),
                    ft.Text("Чат с ИИ", size=16, weight=ft.FontWeight.W_600),
                    ft.Container(width=16),
                    self.mode_dropdown,
                    ft.Container(expand=True),
                    self.sessions_dropdown,
                    ft.IconButton(
                        icon=ft.Icons.ADD_COMMENT_OUTLINED,
                        tooltip="Новая сессия",
                        on_click=self._handle_new_session,
                        icon_size=18,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_SWEEP_OUTLINED,
                        tooltip="Очистить историю",
                        on_click=self._handle_clear,
                        icon_size=18,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )

        # Панель ввода
        input_bar = ft.Container(
            content=ft.Row(
                [self.message_input, send_btn],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        )

        super().__init__(
            controls=[
                chat_header,
                ft.Divider(height=1, thickness=0.5),
                ft.Container(
                    content=ft.Column(
                        [self.messages_list, self.typing_indicator],
                        expand=True,
                        spacing=0,
                    ),
                    expand=True,
                ),
                ft.Divider(height=1, thickness=0.5),
                input_bar,
            ],
            spacing=0,
            expand=True,
            **kwargs,
        )

    def add_message(self, role: str, content: str, timestamp: str = None):
        """Добавить сообщение в список."""
        msg = ChatMessage(
            role=role,
            content=content,
            timestamp=timestamp,
            on_copy=self._on_copy_message if role == "assistant" else None,
            on_reply=self._on_reply_to_message if role == "assistant" else None,
            agent_name=self._agent_name if role == "assistant" else None,
        )
        self.messages_list.controls.append(msg)

    def _on_copy_message(self, content: str):
        """Скопировать сообщение или выделенный фрагмент в буфер."""
        if self._page and content:
            self._page.set_clipboard_text(content)
            self._page.show_dialog(
                ft.SnackBar(content=ft.Text("Скопировано"), duration=1500)
            )
            self._page.update()

    def _on_reply_to_message(self):
        """Ответить: вставить из буфера (выделенный текст) или весь ответ."""
        if not self._page:
            return
        try:
            text = self._page.get_clipboard_text()
        except Exception:
            text = ""
        prefix = f'По поводу «{text}»: ' if text else ""
        self.message_input.value = prefix + (self.message_input.value or "")
        self.message_input.focus()
        self.update()

    def show_typing(self, show: bool = True):
        """Показать/скрыть индикатор набора текста."""
        self.typing_indicator.visible = show

    def clear_messages(self):
        """Очистить все сообщения."""
        clear_handlers()
        self.messages_list.controls.clear()

    def set_sessions(self, sessions: list):
        """Обновить список сессий. Отображение: default → Основной чат, остальные — как есть (dd.mm.yyyy или dd.mm.yyyy.N)."""
        def _label(sid: str) -> str:
            if sid == "default":
                return "Основной чат"
            return sid
        self.sessions_dropdown.options = [ft.dropdown.Option(s, _label(s)) for s in sessions]

    def _handle_send(self, e):
        message = self.message_input.value
        if message and message.strip():
            self.message_input.value = ""
            self.message_input.update()
            if self._on_send:
                self._on_send(message.strip())

    def _handle_new_session(self, e):
        if self._on_new_session:
            self._on_new_session()

    def _handle_session_change(self, e: ft.ControlEvent):
        if self._on_session_select and e.control.value is not None:
            self._on_session_select(e.control.value)

    def _handle_clear(self, e):
        self.clear_messages()
        self.update()
