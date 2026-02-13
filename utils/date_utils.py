"""
Sphere — Утилиты для работы с датами.
"""

from datetime import datetime, date, timedelta
from typing import Optional


def format_relative(dt: datetime) -> str:
    """Форматировать дату относительно текущего времени."""
    now = datetime.now()
    diff = now - dt

    if diff.days == 0:
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        if hours > 0:
            return f"{hours} ч. назад"
        elif minutes > 0:
            return f"{minutes} мин. назад"
        else:
            return "только что"
    elif diff.days == 1:
        return "вчера"
    elif diff.days < 7:
        return f"{diff.days} дн. назад"
    elif diff.days < 30:
        weeks = diff.days // 7
        return f"{weeks} нед. назад"
    elif diff.days < 365:
        months = diff.days // 30
        return f"{months} мес. назад"
    else:
        return dt.strftime("%d.%m.%Y")


def format_date_ru(d: date) -> str:
    """Форматировать дату на русском."""
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return f"{d.day} {months[d.month - 1]} {d.year}"


def format_time(dt: datetime) -> str:
    """Форматировать время."""
    return dt.strftime("%H:%M")


def parse_date(text: str) -> Optional[datetime]:
    """Попробовать распарсить дату из строки."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    return None


def is_overdue(due_date_str: str) -> bool:
    """Проверить, просрочена ли дата."""
    dt = parse_date(due_date_str)
    if dt:
        return dt < datetime.now()
    return False


def get_week_range(d: date = None) -> tuple:
    """Получить начало и конец недели."""
    if d is None:
        d = date.today()
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_month_range(d: date = None) -> tuple:
    """Получить начало и конец месяца."""
    if d is None:
        d = date.today()
    start = d.replace(day=1)
    if d.month == 12:
        end = d.replace(year=d.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = d.replace(month=d.month + 1, day=1) - timedelta(days=1)
    return start, end
