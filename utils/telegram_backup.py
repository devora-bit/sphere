"""
Sphere — выгрузка и скачивание бекапа через Telegram бота.

Бекап — один JSON файл (заметки, задачи, события, документы). Текст весит мало.
"""

import asyncio
from pathlib import Path
from typing import Tuple, Optional

from loguru import logger


async def send_backup_to_telegram(
    bot_token: str,
    chat_id: str,
    file_path: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Отправить файл бекапа в Telegram. Возвращает (file_id, None) или (None, error_message).
    """
    path = Path(file_path)
    if not path.exists():
        return None, "Файл не найден"
    try:
        from telegram import Bot
        bot = Bot(token=bot_token)
        with open(path, "rb") as f:
            msg = await bot.send_document(
                chat_id=chat_id,
                document=f,
                filename=path.name,
                read_timeout=60,
                write_timeout=60,
            )
        file_id = msg.document.file_id if msg.document else None
        if not file_id:
            return None, "Не удалось получить file_id"
        return file_id, None
    except ImportError:
        return None, "Установите python-telegram-bot"
    except Exception as e:
        logger.exception("Telegram send_backup")
        return None, str(e)


async def get_backup_from_telegram(
    bot_token: str,
    file_id: str,
    dest_path: str,
) -> Tuple[bool, Optional[str]]:
    """
    Скачать файл из Telegram по file_id. Возвращает (True, None) или (False, error_message).
    """
    try:
        from telegram import Bot
        bot = Bot(token=bot_token)
        file = await bot.get_file(file_id)
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        await file.download_to_drive(dest_path)
        return True, None
    except ImportError:
        return False, "Установите python-telegram-bot"
    except Exception as e:
        logger.exception("Telegram get_backup")
        return False, str(e)
