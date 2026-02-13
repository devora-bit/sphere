"""
Sphere — Компонент сообщения чата.
"""

import flet as ft
import uuid
from datetime import datetime

# Реестр колбэков — Flet не сериализует bound methods, храним вызовы по ключу
_copy_handlers: dict = {}
_reply_handlers: dict = {}


def _invoke_copy(handler_key: str):
    if handler_key and handler_key in _copy_handlers:
        cb, content = _copy_handlers[handler_key]
        if cb:
            cb(content)


def _invoke_reply(handler_key: str):
    if handler_key and handler_key in _reply_handlers:
        cb = _reply_handlers[handler_key]
        if cb:
            cb()


def clear_handlers():
    """Очистить реестр (вызывать при сбросе чата)."""
    _copy_handlers.clear()
    _reply_handlers.clear()


class ChatMessage(ft.Container):
    """Одно сообщение в чате (пользователь или ИИ)."""

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: str = None,
        on_copy: callable = None,
        on_reply: callable = None,
        agent_name: str = None,
        **kwargs,
    ):
        self.role = role
        self.message_content = content
        is_user = role == "user"
        self._agent_name = (agent_name or "Sphere AI").strip() or "Sphere AI"

        # Регистрируем колбэки под ключами (избегаем сериализации bound methods)
        copy_key = str(uuid.uuid4()) if on_copy else None
        reply_key = str(uuid.uuid4()) if on_reply else None
        if copy_key:
            _copy_handlers[copy_key] = (on_copy, content)
        if reply_key:
            _reply_handlers[reply_key] = on_reply

        # Аватар
        avatar = ft.CircleAvatar(
            content=ft.Icon(
                ft.Icons.PERSON if is_user else ft.Icons.AUTO_AWESOME,
                size=16,
                color=ft.Colors.ON_SURFACE,
            ),
            radius=16,
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.ON_SURFACE),
        )

        # Имя — ON_SURFACE для читаемости на светлом и тёмном фоне
        name = ft.Text(
            "Вы" if is_user else self._agent_name,
            size=13,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.ON_SURFACE,
        )

        # Время
        time_text = ft.Text(
            timestamp or datetime.now().strftime("%H:%M"),
            size=11,
            color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
        )

        # Текст сообщения — явный цвет для читаемости
        on_surface = ft.Colors.ON_SURFACE
        body_style = ft.TextStyle(color=on_surface, size=14)
        message_text = ft.Markdown(
            content,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=lambda e: None,  # TODO: handle links
            md_style_sheet=ft.MarkdownStyleSheet(
                p_text_style=body_style,
                h1_text_style=body_style,
                h2_text_style=body_style,
                h3_text_style=body_style,
                h4_text_style=body_style,
                h5_text_style=body_style,
                h6_text_style=body_style,
                code_text_style=body_style,
                strong_text_style=body_style,
                em_text_style=body_style,
                a_text_style=body_style,
            ),
        ) if not is_user else ft.Text(
            content,
            selectable=True,
            size=14,
            color=on_surface,
        )

        # Кнопки действий — icon_color для видимости на светлом фоне
        copy_btn = ft.IconButton(
            icon=ft.Icons.CONTENT_COPY_OUTLINED,
            icon_size=14,
            icon_color=ft.Colors.ON_SURFACE,
            tooltip="Копировать ответ",
            style=ft.ButtonStyle(padding=4),
            data=copy_key,
            on_click=lambda e: _invoke_copy(e.control.data) if e.control.data else None,
        )
        reply_btn = ft.IconButton(
            icon=ft.Icons.REPLY_OUTLINED,
            icon_size=14,
            icon_color=ft.Colors.ON_SURFACE,
            tooltip="Ответить (выделите текст, Ctrl+C, затем нажмите — или скопируйте весь ответ)",
            style=ft.ButtonStyle(padding=4),
            data=reply_key,
            on_click=lambda e: _invoke_reply(e.control.data) if e.control.data else None,
        )
        actions = ft.Row(
            [copy_btn, reply_btn],
            spacing=0,
            visible=not is_user and (on_copy is not None or on_reply is not None),
        )

        bubble = ft.Container(
            content=ft.Column(
                [
                    ft.Row([avatar, name, time_text], spacing=8, alignment=ft.MainAxisAlignment.START),
                    ft.Container(
                        content=message_text,
                        padding=ft.padding.only(left=40),
                    ),
                    ft.Container(
                        content=actions,
                        padding=ft.padding.only(left=36),
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.all(12),
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE) if is_user else ft.Colors.TRANSPARENT,
        )

        super().__init__(
            content=bubble,
            padding=ft.padding.symmetric(horizontal=16, vertical=2),
            **kwargs,
        )

    def _toggle_actions(self, e, actions):
        actions.visible = e.data == "true"
        actions.update()


class TypingIndicator(ft.Container):
    """Индикатор «ИИ печатает...»."""

    def __init__(self, **kwargs):
        super().__init__(
            content=ft.Row(
                [
        ft.CircleAvatar(
                    content=ft.Icon(
                        ft.Icons.AUTO_AWESOME,
                        size=16,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    radius=16,
                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.ON_SURFACE),
                ),
                    ft.Text(
                        "Sphere AI думает...",
                        size=13,
                        italic=True,
                        color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
                    ),
                    ft.ProgressRing(width=16, height=16, stroke_width=2),
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=28, vertical=8),
            **kwargs,
        )
