"""
Sphere — Шина событий для межмодульного взаимодействия.

Позволяет модулям обмениваться сообщениями без прямых зависимостей.
"""

import asyncio
from typing import Callable, Dict, List, Any
from loguru import logger


class EventBus:
    """Простая pub/sub шина событий."""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._async_listeners: Dict[str, List[Callable]] = {}

    def on(self, event: str, callback: Callable):
        """Подписаться на событие (синхронный обработчик)."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
        logger.debug(f"Подписка на событие: {event}")

    def on_async(self, event: str, callback: Callable):
        """Подписаться на событие (асинхронный обработчик)."""
        if event not in self._async_listeners:
            self._async_listeners[event] = []
        self._async_listeners[event].append(callback)
        logger.debug(f"Async подписка на событие: {event}")

    def off(self, event: str, callback: Callable):
        """Отписаться от события."""
        if event in self._listeners:
            self._listeners[event] = [cb for cb in self._listeners[event] if cb != callback]
        if event in self._async_listeners:
            self._async_listeners[event] = [cb for cb in self._async_listeners[event] if cb != callback]

    def emit(self, event: str, data: Any = None):
        """Испустить событие (синхронно)."""
        logger.debug(f"Событие: {event}")
        for cb in self._listeners.get(event, []):
            try:
                cb(data)
            except Exception as e:
                logger.error(f"Ошибка обработчика {event}: {e}")

    async def emit_async(self, event: str, data: Any = None):
        """Испустить событие (асинхронно)."""
        logger.debug(f"Async событие: {event}")
        # Синхронные обработчики
        for cb in self._listeners.get(event, []):
            try:
                cb(data)
            except Exception as e:
                logger.error(f"Ошибка обработчика {event}: {e}")
        # Асинхронные обработчики
        for cb in self._async_listeners.get(event, []):
            try:
                await cb(data)
            except Exception as e:
                logger.error(f"Ошибка async обработчика {event}: {e}")


# Предопределённые события
class Events:
    # Навигация
    MODULE_CHANGED = "module:changed"

    # Чат
    CHAT_MESSAGE_SENT = "chat:message_sent"
    CHAT_RESPONSE_RECEIVED = "chat:response_received"
    CHAT_SESSION_CHANGED = "chat:session_changed"

    # Заметки
    NOTE_CREATED = "note:created"
    NOTE_UPDATED = "note:updated"
    NOTE_DELETED = "note:deleted"

    # Задачи
    TASK_CREATED = "task:created"
    TASK_UPDATED = "task:updated"
    TASK_COMPLETED = "task:completed"
    TASK_DELETED = "task:deleted"

    # Календарь
    EVENT_CREATED = "event:created"
    EVENT_UPDATED = "event:updated"
    EVENT_DELETED = "event:deleted"
    EVENT_REMINDER = "event:reminder"

    # База знаний
    DOCUMENT_ADDED = "knowledge:document_added"
    DOCUMENT_PROCESSED = "knowledge:document_processed"

    # Поиск
    SEARCH_PERFORMED = "search:performed"

    # Уведомления
    NOTIFICATION_SEND = "notification:send"

    # Общие
    DATA_CHANGED = "data:changed"
    ERROR = "app:error"


# Глобальный экземпляр
event_bus = EventBus()
