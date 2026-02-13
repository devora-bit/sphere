#!/usr/bin/env python3
"""
Подсчёт строк и символов в Python-файлах проекта (без venv, __pycache__).
Для вставки в DEVLOG.md.
"""

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EXCLUDE = {"venv", "__pycache__", ".git"}


def main():
    total_lines = 0
    total_chars = 0
    for p in BASE.rglob("*.py"):
        if any(ex in p.parts for ex in EXCLUDE):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        lines = len(text.splitlines())
        total_lines += lines
        total_chars += len(text)
    print(f"Строк: {total_lines:,} | Символов: {total_chars:,}".replace(",", " "))
    print(f"\n*Строк: {total_lines:,} | Символов: {total_chars:,}*".replace(",", " "))


if __name__ == "__main__":
    main()
