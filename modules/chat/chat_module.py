"""
Sphere — Модуль чата с ИИ.
"""

import flet as ft
import asyncio
from datetime import datetime
from typing import Optional

from core.ai_engine import AIEngine
from core.event_bus import event_bus, Events
from database import Database
from ui.layouts.chat_layout import ChatLayout
from loguru import logger


class ChatModule:
    """Модуль чата с ИИ-ассистентом. ИИ ищет по заметкам, задачам и документам пользователя."""

    def __init__(self, db: Database, ai_engine: AIEngine, page: ft.Page, vector_db=None, config=None):
        self.db = db
        self.ai = ai_engine
        self.page = page
        self.vector_db = vector_db
        self.config = config
        self.current_session = "default"
        self.layout: Optional[ChatLayout] = None

    def build(self) -> ChatLayout:
        """Построить интерфейс чата."""
        mode = (self.config.ai.search_mode if self.config else "hybrid")
        if mode not in ("knowledge", "hybrid", "model_only"):
            mode = "hybrid"
        self.layout = ChatLayout(
            page=self.page,
            on_send=self._on_send_message,
            on_new_session=self._on_new_session,
            on_session_select=self._on_session_select,
            ai_mode=mode,
            on_ai_mode_change=self._on_ai_mode_change,
        )
        # Загрузить историю
        self._load_history()
        self._load_sessions()
        return self.layout

    def _load_history(self):
        """Загрузить историю чата из БД."""
        if not self.layout:
            return
        self.layout.clear_messages()
        messages = self.db.get_chat_history(self.current_session)
        for msg in messages:
            self.layout.add_message(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("created_at", "")[:16].replace("T", " "),
            )
        # Загрузить историю в AI Engine
        self.ai.load_history(messages)

    def _load_sessions(self):
        """Загрузить список сессий."""
        if not self.layout:
            return
        sessions = self.db.get_chat_sessions()
        if "default" not in sessions:
            sessions.insert(0, "default")
        self.layout.set_sessions(sessions)

    def send_message(self, message: str):
        """Отправить сообщение программно (например, из поиска в хедере)."""
        if message and message.strip():
            self._on_send_message(message.strip())

    def _on_send_message(self, message: str):
        """Обработка отправки сообщения."""
        if not self.layout:
            return

        # Добавляем сообщение пользователя в UI
        now = datetime.now().strftime("%H:%M")
        self.layout.add_message("user", message, now)

        # Сохраняем в БД
        self.db.add_chat_message(
            role="user",
            content=message,
            session_id=self.current_session,
        )

        # Показываем индикатор загрузки
        self.layout.show_typing(True)
        self.layout.update()

        # Сессия на момент запроса — сохраняем ответ в неё, даже если пользователь переключится
        session_for_request = self.current_session
        self.page.run_task(self._get_ai_response, message, session_for_request)

    async def _get_ai_response(self, message: str, session_id: str = None):
        """Получить ответ от ИИ (асинхронно). session_id — куда сохранять, даже при смене сессии."""
        target_session = session_id or self.current_session
        try:
            # Собираем контекст в зависимости от режима
            mode = self.config.ai.search_mode if self.config else "hybrid"
            context = self._gather_context(user_message=message, mode=mode)

            # Получаем ответ
            response = await self.ai.chat(message, context, mode=mode)

            # Скрываем индикатор
            self.layout.show_typing(False)

            # Добавляем ответ в UI (только если это всё ещё активная сессия)
            now = datetime.now().strftime("%H:%M")
            if self.current_session == target_session:
                self.layout.add_message("assistant", response, now)
                self.layout.update()

            # Сохраняем в БД в ту сессию, для которой был запрос
            self.db.add_chat_message(
                role="assistant",
                content=response,
                session_id=target_session,
                provider=self.ai.current_provider,
            )

            # Событие
            event_bus.emit(Events.CHAT_RESPONSE_RECEIVED, {
                "message": message,
                "response": response,
            })

        except Exception as e:
            logger.error(f"Ошибка AI: {e}")
            self.layout.show_typing(False)
            err_msg = f"Произошла ошибка: {e}\n\nПроверьте, что Ollama запущена: `ollama serve`"
            if self.current_session == target_session:
                self.layout.add_message("assistant", err_msg)
            self.db.add_chat_message(
                role="assistant",
                content=err_msg,
                session_id=target_session,
            )
            self.layout.update()

    def _gather_context(self, user_message: str = "", mode: str = "hybrid") -> dict:
        """Собрать контекст в зависимости от режима.
        knowledge — только база знаний (поиск по заметкам, задачам, документам)
        hybrid — база знаний + задачи/события + знания модели
        model_only — пустой контекст, только модель
        """
        if mode == "model_only":
            return {}

        context = {}
        # Задачи и события — только в гибриде
        if mode == "hybrid":
            try:
                tasks = self.db.get_tasks(status="todo", limit=5)
                if tasks:
                    context["tasks"] = tasks
            except Exception:
                pass
            try:
                from datetime import date
                today = date.today().isoformat()
                events = self.db.get_events(start_from=today, limit=5)
                if events:
                    context["events"] = events
            except Exception:
                pass

        # Поиск по данным пользователя — в knowledge и hybrid
        if user_message and len(user_message.strip()) >= 2:
            query = user_message.strip()
            try:
                notes = self.db.search_notes(query)
                if notes:
                    context["search_notes"] = notes
            except Exception:
                pass
            try:
                tasks_found = self.db.search_tasks(query)
                if tasks_found:
                    context["search_tasks"] = tasks_found
            except Exception:
                pass
            if self.vector_db and self.vector_db.is_available:
                try:
                    docs = self.vector_db.search(query, n_results=5)
                    if docs:
                        context["search_docs"] = docs
                except Exception:
                    pass
        return context

    def _generate_session_id(self) -> str:
        """Сгенерировать ID сессии: dd.mm.yyyy или dd.mm.yyyy.N (первый чат за день — без суффикса)."""
        date_str = datetime.now().strftime("%d.%m.%Y")
        sessions = self.db.get_chat_sessions()
        today_sessions = [
            s for s in sessions
            if s == date_str or (s.startswith(date_str + ".") and s[len(date_str) + 1 :].isdigit())
        ]
        if not today_sessions:
            return date_str
        numbers = []
        for s in today_sessions:
            if s == date_str:
                numbers.append(-1)
            else:
                suffix = s[len(date_str) + 1 :]
                if suffix.isdigit():
                    numbers.append(int(suffix))
        next_num = max(numbers) + 1 if numbers else 0
        return f"{date_str}.{next_num}"

    def _on_new_session(self):
        """Создать новую сессию чата."""
        session_id = self._generate_session_id()
        self.current_session = session_id
        self.ai.clear_history()
        self.layout.clear_messages()
        self._load_sessions()
        self.layout.sessions_dropdown.value = session_id
        self.layout.update()

    def _on_session_select(self, session_id: str):
        """Переключиться на другую сессию."""
        self.current_session = session_id
        self.ai.clear_history()
        self.layout.show_typing(False)
        self._load_history()
        self.layout.update()

    def _on_ai_mode_change(self, mode: str):
        """Изменить режим общения с ИИ."""
        if self.config and mode in ("knowledge", "hybrid", "model_only"):
            self.config.ai.search_mode = mode
            self.config.save()
