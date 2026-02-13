"""
Sphere — Модуль уведомлений.
"""

import asyncio
import platform
from typing import Optional
from loguru import logger

from config import AppConfig
from core.event_bus import event_bus, Events


class NotificationsModule:
    """Модуль уведомлений (локальные + Telegram)."""

    def __init__(self, config: AppConfig):
        self.config = config
        self._telegram_bot = None
        self._setup_listeners()

    def _setup_listeners(self):
        """Подписаться на события для автоматических уведомлений."""
        event_bus.on(Events.TASK_COMPLETED, self._on_task_completed)
        event_bus.on(Events.EVENT_REMINDER, self._on_event_reminder)
        event_bus.on(Events.NOTIFICATION_SEND, self._on_notification_send)

    def _on_task_completed(self, data):
        if data:
            self.send_local(
                title="Задача выполнена",
                message=f"Задача #{data.get('id', '')} отмечена как выполненная.",
            )

    def _on_event_reminder(self, data):
        if data:
            self.send_local(
                title="Напоминание",
                message=data.get("title", "Скоро событие!"),
            )

    def _on_notification_send(self, data):
        if data:
            self.send_local(
                title=data.get("title", "Sphere"),
                message=data.get("message", ""),
            )

    def send_local(self, title: str, message: str):
        """Отправить локальное уведомление macOS."""
        system = platform.system()
        try:
            if system == "Darwin":
                try:
                    import pync
                    pync.notify(
                        message,
                        title=title,
                        app_icon="",
                        sound="default",
                    )
                    logger.debug(f"Уведомление: {title}")
                    return
                except ImportError:
                    pass

                # Fallback: osascript
                import subprocess
                subprocess.run(
                    ["osascript", "-e",
                     f'display notification "{message}" with title "{title}"'],
                    capture_output=True,
                )
            elif system == "Linux":
                import subprocess
                subprocess.run(["notify-send", title, message], capture_output=True)
            elif system == "Windows":
                try:
                    from plyer import notification
                    notification.notify(title=title, message=message, timeout=5)
                except ImportError:
                    pass
        except Exception as e:
            logger.error(f"Ошибка уведомления: {e}")

    async def send_telegram(self, message: str):
        """Отправить сообщение через Telegram бота."""
        if not self.config.telegram.enabled:
            return
        if not self.config.telegram.bot_token or not self.config.telegram.chat_id:
            logger.warning("Telegram бот не настроен")
            return
        try:
            from telegram import Bot
            bot = Bot(token=self.config.telegram.bot_token)
            await bot.send_message(
                chat_id=self.config.telegram.chat_id,
                text=message,
                parse_mode="Markdown",
            )
            logger.debug("Telegram сообщение отправлено")
        except ImportError:
            logger.warning("python-telegram-bot не установлен")
        except Exception as e:
            logger.error(f"Ошибка Telegram: {e}")

    async def check_upcoming_events(self, db):
        """Проверить ближайшие события и отправить напоминания."""
        from datetime import datetime, timedelta
        now = datetime.now()
        soon = now + timedelta(minutes=15)
        events = db.get_events(
            start_from=now.isoformat(),
            start_to=soon.isoformat(),
        )
        for ev in events:
            event_bus.emit(Events.EVENT_REMINDER, {
                "title": f"Через 15 минут: {ev['title']}",
                "event": ev,
            })
