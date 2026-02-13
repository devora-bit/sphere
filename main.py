"""
Sphere AI Assistant — Точка входа.

Запуск: python main.py
Или:    flet run main.py
"""

import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

import flet as ft
from loguru import logger

from app import SphereApp
from config import DATA_DIR

# Настройка логирования
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
logger.add(
    DATA_DIR / "sphere.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
)


def main(page: ft.Page):
    """Главная функция — вызывается Flet."""
    # Иконка окна — задаём сразу при создании page (до контента), абсолютный путь
    icon_path = Path(__file__).resolve().parent / "assets" / "icon.png"
    if icon_path.exists():
        page.window.icon = str(icon_path)

    app = SphereApp()

    async def close_app():
        app.shutdown()
        await page.window.destroy()

    def on_window_event(e: ft.WindowEvent):
        if e.type == ft.WindowEventType.CLOSE:
            page.run_task(close_app)

    page.window.prevent_close = True
    page.window.on_event = on_window_event

    # Запуск приложения
    app.main(page)


if __name__ == "__main__":
    logger.info("Запуск Sphere AI Assistant...")
    ft.run(main, assets_dir="assets")
