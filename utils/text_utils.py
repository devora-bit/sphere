"""
Sphere — Утилиты для обработки текста.
"""

import re
from typing import List


def clean_text(text: str) -> str:
    """Очистить текст от лишних пробелов и спецсимволов."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Обрезать текст до заданной длины."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def extract_tags(text: str) -> List[str]:
    """Извлечь хештеги из текста (#tag)."""
    return re.findall(r"#(\w+)", text)


def markdown_to_plain(text: str) -> str:
    """Простое преобразование Markdown в plain text."""
    # Убираем заголовки
    text = re.sub(r"#{1,6}\s*", "", text)
    # Убираем жирный/курсив
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}(.*?)_{1,3}", r"\1", text)
    # Убираем ссылки
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Убираем код
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
    # Убираем списки
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    return clean_text(text)


def split_into_sentences(text: str) -> List[str]:
    """Разбить текст на предложения."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def word_count(text: str) -> int:
    """Посчитать количество слов."""
    return len(text.split())


def highlight_query(text: str, query: str) -> str:
    """Подсветить поисковый запрос в тексте (для Markdown)."""
    if not query:
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f"**{m.group()}**", text)
