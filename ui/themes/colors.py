"""
Sphere — Цветовая палитра приложения.
"""

import flet as ft


# Основные цвета бренда
class SphereColors:
    # Основной цвет — тёмная тема (#626880)
    PRIMARY = "#626880"
    PRIMARY_LIGHT = "#7A8199"
    PRIMARY_DARK = "#4D5466"

    # Акцентный цвет — светлая тема (#C6D0F5)
    ACCENT = "#C6D0F5"
    ACCENT_LIGHT = "#D8DFF7"
    ACCENT_DARK = "#A8B3E8"

    # Фоновые цвета (тёмная тема)
    DARK_BG = "#0D1117"
    DARK_SURFACE = "#161B22"
    DARK_CARD = "#1C2128"
    DARK_BORDER = "#30363D"

    # Фоновые цвета (светлая тема)
    LIGHT_BG = "#FAFBFC"
    LIGHT_SURFACE = "#FFFFFF"
    LIGHT_CARD = "#F6F8FA"
    LIGHT_BORDER = "#D0D7DE"

    # Статусные цвета
    SUCCESS = ft.Colors.GREEN_400
    WARNING = ft.Colors.AMBER_400
    ERROR = ft.Colors.RED_400
    INFO = ft.Colors.BLUE_400

    # Приоритеты задач
    PRIORITY_HIGH = ft.Colors.RED_400
    PRIORITY_MEDIUM = ft.Colors.AMBER_400
    PRIORITY_LOW = ft.Colors.GREEN_400

    # Статусы задач
    STATUS_TODO = ft.Colors.BLUE_GREY_400
    STATUS_IN_PROGRESS = ft.Colors.BLUE_400
    STATUS_DONE = ft.Colors.GREEN_400

    # Текст
    DARK_TEXT_PRIMARY = "#E6EDF3"
    DARK_TEXT_SECONDARY = "#8B949E"
    LIGHT_TEXT_PRIMARY = "#24292F"
    LIGHT_TEXT_SECONDARY = "#57606A"

    # Чат
    USER_BUBBLE = "#4D5466"  # PRIMARY_DARK
    AI_BUBBLE = "#2D333B"
    AI_BUBBLE_LIGHT = "#F0F2F5"
