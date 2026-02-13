"""
Sphere — Главное приложение.

Координирует все модули, управляет навигацией и состоянием.
"""

import webbrowser
from pathlib import Path
from urllib.parse import urlparse, unquote

import flet as ft
from loguru import logger

from config import AppConfig, ensure_directories, DATA_DIR
from version import APP_VERSION
from database import Database
from vector_db import VectorDB
from core.state import AppState, app_state
from core.ai_engine import AIEngine
from core.event_bus import event_bus, Events

from ui.components.sidebar import Sidebar
from ui.components.header import Header
from ui.layouts.dashboard import DashboardLayout
from ui.layouts.about import AboutLayout
from ui.themes.dark import get_dark_theme
from ui.themes.light import get_light_theme
from ui.themes.colors import SphereColors

from modules.chat import ChatModule
from modules.notes import NotesModule
from modules.tasks import TasksModule
from modules.calendar import CalendarModule
from modules.knowledge import KnowledgeModule
from modules.notifications import NotificationsModule
from utils.file_utils import create_backup, export_data_to_json, export_notes_to_files
from utils.importers import import_markdown_files
from utils.updater import check_for_updates, apply_update, is_git_repo


class SphereApp:
    """Главное приложение Sphere AI Assistant."""

    def __init__(self):
        # Конфигурация
        self.config = AppConfig.load()
        self.state = app_state
        self.state.config = self.config

        # Базы данных
        self.db = Database()
        self.vector_db = VectorDB()

        # AI Engine
        self.ai_engine = AIEngine(self.config)

        # Модули (инициализируются при запуске)
        self.chat_module = None
        self.notes_module = None
        self.tasks_module = None
        self.calendar_module = None
        self.knowledge_module = None
        self.notifications_module = None

        # UI
        self.page: ft.Page = None
        self.sidebar: Sidebar = None
        self.header: Header = None
        self.main_content: ft.Container = None

        # Кеш построенных модулей
        self._module_views = {}

    def initialize(self):
        """Инициализировать все компоненты."""
        logger.info("Инициализация Sphere...")
        ensure_directories()
        self.db.initialize()
        self.vector_db.initialize()

        # Инициализируем модули
        self.chat_module = ChatModule(self.db, self.ai_engine, self.page, self.vector_db, self.config)
        self.notes_module = NotesModule(self.db, self.page)
        self.tasks_module = TasksModule(self.db, self.page)
        self.calendar_module = CalendarModule(self.db, self.page)
        self.knowledge_module = KnowledgeModule(self.db, self.vector_db, self.ai_engine, self.page)
        self.notifications_module = NotificationsModule(self.config)

        # Обновить счётчики
        self.state.update_counts(self.db)

        logger.info("Sphere инициализирован")

    def main(self, page: ft.Page):
        """Точка входа — вызывается Flet."""
        self.page = page

        # Патч launch_url: в Flet 0.80+ это async, но вызывается синхронно из Markdown.
        # Заменяем на webbrowser — работает без await и не даёт RuntimeWarning.
        _open_url = webbrowser.open
        page.launch_url = lambda url, **kw: _open_url(url)

        # Настройки окна
        page.title = "Sphere AI Assistant"
        page.padding = 0
        page.spacing = 0
        page.window.width = self.config.ui.window_width
        page.window.height = self.config.ui.window_height
        page.window.min_width = 800
        page.window.min_height = 600
        # Иконка окна (глобус). Flet на macOS/Windows часто требует абсолютный путь (issue #3438).
        _icon_path = Path(__file__).resolve().parent / "assets" / "icon.png"
        if _icon_path.exists():
            page.window.icon = str(_icon_path)

        # Тема
        is_dark = self.config.ui.theme_mode == "dark"
        page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        page.theme = get_light_theme()
        page.dark_theme = get_dark_theme()

        # Фон окна: светлая — лавандовая, тёмная — глубокий тёмный
        if is_dark:
            page.bgcolor = SphereColors.DARK_BG
        else:
            page.bgcolor = SphereColors.ACCENT

        # Инициализация
        self.initialize()

        # Построить UI
        self._build_ui()

        # Показать начальный модуль
        self._navigate_to("chat")

        # Проверка обновлений при запуске (если включено)
        if self.config.auto_update_on_start and is_git_repo():
            self.page.run_task(self._check_updates_async, show_only_if_available=True)

        logger.info("UI построен, приложение запущено")

    def _build_ui(self):
        """Построить основной интерфейс."""
        # Sidebar
        self.sidebar = Sidebar(on_module_change=self._on_module_change)

        # Header
        self.header = Header(
            on_search=self._on_global_search,
            on_theme_toggle=self._on_theme_toggle,
            on_notifications=self._on_notifications_click,
            on_export_md=self._export_md,
            on_import_md=self._import_md,
            on_export_json=self._do_export,
            on_backup=self._do_backup,
            on_about=self._show_about_dialog,
            version=APP_VERSION,
        )
        self.header.set_theme_icon(self.page.theme_mode == ft.ThemeMode.DARK)

        # Область контента — отдельная светлая панель поверх лавандового фона
        self.main_content = ft.Container(
            expand=True,
            padding=0,
            bgcolor=ft.Colors.SURFACE,
        )

        # Собираем макет
        self.page.appbar = self.header

        self.page.add(
            ft.Row(
                [
                    self.sidebar,
                    ft.VerticalDivider(width=1, thickness=0.5, color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
                    ft.Column(
                        [self.main_content],
                        expand=True,
                        spacing=0,
                    ),
                ],
                expand=True,
                spacing=0,
            )
        )

    def _get_module_view(self, module_name: str) -> ft.Control:
        """Получить или построить вид модуля."""
        # О проекте — всегда пересобираем, чтобы Dev Log был актуальным
        if module_name == "about":
            return AboutLayout(version=APP_VERSION)
        if module_name not in self._module_views:
            builder = {
                "dashboard": lambda: DashboardLayout(
                    state=self.state,
                    on_navigate=self._navigate_to,
                ),
                "chat": lambda: self.chat_module.build(),
                "notes": lambda: self.notes_module.build(),
                "tasks": lambda: self.tasks_module.build(),
                "calendar": lambda: self.calendar_module.build(),
                "knowledge": lambda: self.knowledge_module.build(),
                "settings": lambda: self._build_settings_view(),
                "about": lambda: AboutLayout(version=APP_VERSION),
            }
            build_fn = builder.get(module_name)
            if build_fn:
                self._module_views[module_name] = build_fn()
            else:
                self._module_views[module_name] = ft.Text(f"Модуль '{module_name}' не найден")
        return self._module_views[module_name]

    def _navigate_to(self, module_name: str):
        """Перейти к модулю."""
        self.state.current_module = module_name
        view = self._get_module_view(module_name)
        self.main_content.content = view
        self.sidebar.select_module(module_name)
        self.page.update()
        event_bus.emit(Events.MODULE_CHANGED, {"module": module_name})

    def _on_module_change(self, module_name: str):
        """Обработчик смены модуля из sidebar."""
        self._navigate_to(module_name)

    def _on_global_search(self, query: str):
        """Спросить ИИ по данным пользователя — переход в чат и отправка запроса."""
        self._navigate_to("chat")
        if self.chat_module and query.strip():
            self.chat_module.send_message(query)
        self.page.update()

    def _on_theme_toggle(self):
        """Переключить тему."""
        if self.page.theme_mode == ft.ThemeMode.DARK:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.config.ui.theme_mode = "light"
        else:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.config.ui.theme_mode = "dark"

        # Синхронизируем фон окна с режимом
        if self.page.theme_mode == ft.ThemeMode.DARK:
            self.page.bgcolor = SphereColors.DARK_BG
        else:
            self.page.bgcolor = SphereColors.ACCENT

        self.header.set_theme_icon(self.page.theme_mode == ft.ThemeMode.DARK)
        self.config.save()
        self.page.update()

    def _on_notifications_click(self, e):
        """Показать панель уведомлений."""
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text("Нет новых уведомлений"),
                duration=2000,
            )
        )

    def _show_about_dialog(self, e=None):
        """Показать диалог «О программе Sphere»."""
        about_content = ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.SHIELD_OUTLINED, size=28, color=ft.Colors.PRIMARY),
                            ft.Text(
                                "Sphere — локальный AI‑ассистент",
                                size=18,
                                weight=ft.FontWeight.W_600,
                            ),
                                ],
                                spacing=10,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Container(height=8),
                            ft.Text(
                                "Sphere создан для людей, которые ценят конфиденциальность. "
                                "Все данные хранятся на вашем компьютере. ИИ работает локально (Ollama, DeepSeek) "
                                "или по вашему желанию — через API, без передачи личной информации.",
                                size=13,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Container(height=16),
                            ft.Text("Возможности", size=14, weight=ft.FontWeight.W_600),
                            ft.Container(height=6),
                            ft.Text(
                                "• Чат с ИИ — локальные модели (Ollama), DeepSeek R1\n"
                                "• Заметки — папки, Markdown, закрепление важных\n"
                                "• Задачи — канбан-доска с приоритетами\n"
                                "• Календарь — события и напоминания\n"
                                "• База знаний — RAG, семантический поиск по документам\n"
                                "• ИИ с доступом к вашим данным — можно говорить о чём угодно, ответы точные на основе заметок, задач и документов\n"
                                "• Экспорт/импорт — JSON, Markdown, резервные копии",
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Container(height=16),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.LOCK_OUTLINE, size=18, color=ft.Colors.GREEN_200),
                                        ft.Text(
                                            "Режим «Только локально» — поиск и ИИ без выхода в интернет",
                                            size=12,
                                            color=ft.Colors.GREEN_200,
                                        ),
                                    ],
                                    spacing=8,
                                    wrap=True,
                                ),
                                padding=ft.padding.all(10),
                                border_radius=8,
                                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                            ),
                            ft.Container(height=12),
                            ft.Text(
                                "Telegram: @losstq",
                                size=12,
                                color=ft.Colors.OUTLINE,
                            ),
                        ],
                        spacing=0,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    width=420,
                    height=380,
                ),
            ],
            tight=True,
        )

        about_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"О программе Sphere · {APP_VERSION}"),
            content=about_content,
            actions=[
                ft.TextButton(
                    content=ft.Text("Закрыть"),
                    on_click=lambda e: self.page.pop_dialog(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(about_dialog)

    def _export_md(self, e=None):
        """Экспорт заметок в папку с .md файлами."""
        try:
            path = export_notes_to_files(self.db)
            self.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"Заметки экспортированы в .md: {path}"),
                    duration=4000,
                )
            )
        except Exception as ex:
            logger.error(f"Экспорт .md: {ex}")
            self.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"Ошибка экспорта: {ex}"),
                    duration=3000,
                )
            )

    def _import_md(self, e=None):
        """Запуск выбора папки для импорта .md."""
        self.page.run_task(self._import_md_async)

    async def _import_md_async(self):
        """Импорт .md файлов из выбранной папки."""
        try:
            # FilePicker в Flet 0.80 — сервис, не контрол:
            # создаём временный экземпляр и просто ждём путь к директории.
            path = await ft.FilePicker().get_directory_path(
                dialog_title="Выберите папку с файлами .md"
            )
            if path:
                count = import_markdown_files(path, self.db)
                self.page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(f"Импортировано заметок из .md: {count}"),
                        duration=3000,
                    )
                )
                self._module_views.pop("notes", None)
                if self.state.current_module == "notes":
                    self._navigate_to("notes")
        except Exception as ex:
            logger.error(f"Импорт .md: {ex}")
            self.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"Ошибка импорта: {ex}"),
                    duration=3000,
                )
            )

    def _build_settings_view(self) -> ft.Column:
        """Построить страницу настроек."""
        # AI настройки
        provider_dropdown = ft.Dropdown(
            label="AI-провайдер",
            value=self.config.ai.provider if self.config.ai.provider != "openai" else "ollama",
            options=[
                ft.dropdown.Option("ollama", "Ollama (локально)"),
                ft.dropdown.Option("deepseek", "DeepSeek R1"),
            ],
            on_select=lambda e: self._update_setting("ai.provider", e.control.value),
            width=300,
        )

        ollama_host = ft.TextField(
            label="Ollama хост",
            value=self.config.ai.ollama_host,
            on_change=lambda e: self._update_setting("ai.ollama_host", e.control.value),
            width=300,
        )

        ollama_model = ft.TextField(
            label="Модель Ollama",
            value=self.config.ai.ollama_model,
            on_change=lambda e: self._update_setting("ai.ollama_model", e.control.value),
            width=300,
        )

        deepseek_key = ft.TextField(
            label="DeepSeek API ключ (для провайдера DeepSeek R1)",
            value=self.config.ai.deepseek_api_key or "",
            password=True,
            can_reveal_password=True,
            on_change=lambda e: self._update_setting("ai.deepseek_api_key", e.control.value),
            width=300,
        )

        # Температура: шаг 0.05 для более тонкой настройки
        temperature = ft.Slider(
            min=0,
            max=1,
            divisions=20,  # 0.0, 0.05, ... 1.0
            value=self.config.ai.temperature,
            label="{value}",
            on_change=lambda e: self._update_setting("ai.temperature", e.control.value),
            width=300,
        )

        # Telegram настройки
        tg_enabled = ft.Switch(
            label="Telegram уведомления",
            value=self.config.telegram.enabled,
            on_change=lambda e: self._update_setting("telegram.enabled", e.control.value),
        )

        tg_token = ft.TextField(
            label="Telegram Bot Token",
            value=self.config.telegram.bot_token or "",
            password=True,
            can_reveal_password=True,
            on_change=lambda e: self._update_setting("telegram.bot_token", e.control.value),
            width=300,
        )

        tg_chat_id = ft.TextField(
            label="Telegram Chat ID",
            value=self.config.telegram.chat_id or "",
            on_change=lambda e: self._update_setting("telegram.chat_id", e.control.value),
            width=300,
        )

        # Загрузка локальной модели по ссылке
        self.model_url_field = ft.TextField(
            label="Ссылка на файл (любой формат: .zip, .gguf, .bin и т.д.)",
            value=self.config.ai.local_model_url or "",
            width=400,
            on_change=lambda e: self._update_setting("ai.local_model_url", e.control.value),
        )
        models_link = ft.TextButton(
            content=ft.Text("Каталог моделей Ollama"),
            icon=ft.Icons.OPEN_IN_NEW,
            on_click=self._open_ollama_catalog,
        )
        download_btn = ft.FilledButton(
            content=ft.Text("Загрузить модель"),
            icon=ft.Icons.CLOUD_DOWNLOAD,
            on_click=self._download_model,
        )
        self.model_progress = ft.ProgressBar(
            width=300,
            value=0,
            visible=False,
        )

        # Действия
        save_btn = ft.FilledButton(
            content=ft.Text("Сохранить настройки"),
            icon=ft.Icons.SAVE,
            on_click=self._save_settings,
        )

        backup_btn = ft.ElevatedButton(
            content=ft.Text("Создать бэкап"),
            icon=ft.Icons.BACKUP,
            on_click=self._do_backup,
        )

        export_btn = ft.ElevatedButton(
            content=ft.Text("Экспорт данных (JSON)"),
            icon=ft.Icons.DOWNLOAD,
            on_click=self._do_export,
        )

        check_ai_btn = ft.ElevatedButton(
            content=ft.Text("Проверить подключение AI"),
            icon=ft.Icons.NETWORK_CHECK,
            on_click=self._check_ai_connection,
        )

        return ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.SETTINGS, color=ft.Colors.ON_SURFACE, size=20),
                            ft.Text("Настройки", size=16, weight=ft.FontWeight.W_600),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                ),
                ft.Divider(height=1, thickness=0.5),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Искусственный интеллект", size=16, weight=ft.FontWeight.W_600),
                            provider_dropdown,
                            ollama_host,
                            ollama_model,
                            deepseek_key,
                            ft.Text("Температура", size=13),
                            ft.Row(
                                [
                                    ft.Text("0 — более точные ответы", size=11, color=ft.Colors.with_opacity(0.7, ft.Colors.ON_SURFACE)),
                                    ft.Container(expand=True),
                                    ft.Text("1 — более креативные", size=11, color=ft.Colors.with_opacity(0.7, ft.Colors.ON_SURFACE)),
                                ],
                                spacing=4,
                            ),
                            temperature,
                            ft.Divider(height=16),
                            ft.Text("Загрузка локальной модели по ссылке", size=16, weight=ft.FontWeight.W_600),
                            ft.Row([self.model_url_field, models_link, download_btn], spacing=8),
                            self.model_progress,
                            check_ai_btn,

                            ft.Divider(height=24),
                            ft.Text("Telegram", size=16, weight=ft.FontWeight.W_600),
                            tg_enabled,
                            tg_token,
                            tg_chat_id,

                            ft.Divider(height=24),
                            ft.Text("Данные", size=16, weight=ft.FontWeight.W_600),
                            ft.Row([backup_btn, export_btn], spacing=8),

                            ft.Divider(height=24),
                            ft.Text("Обновления", size=16, weight=ft.FontWeight.W_600),
                            ft.Switch(
                                label="Проверять обновления при запуске",
                                value=self.config.auto_update_on_start,
                                on_change=lambda e: self._update_setting("auto_update_on_start", e.control.value),
                            ),
                            ft.ElevatedButton(
                                content=ft.Text("Проверить обновления"),
                                icon=ft.Icons.UPDATE,
                                on_click=self._check_updates,
                            ),

                            ft.Divider(height=24),
                            save_btn,

                            ft.Divider(height=24),
                            ft.Row(
                                [
                                    ft.Text("Версия", size=13, color=ft.Colors.OUTLINE),
                                    ft.Text(APP_VERSION, size=13, weight=ft.FontWeight.W_500),
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=12,
                    ),
                    padding=ft.padding.all(24),
                    expand=True,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
        )

    def _update_setting(self, key: str, value):
        """Обновить настройку в конфигурации."""
        parts = key.split(".")
        obj = self.config
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)

    def _save_settings(self, e):
        """Сохранить настройки."""
        self.config.save()
        # Пересоздаём AI Engine с новыми настройками
        self.ai_engine = AIEngine(self.config)
        if self.chat_module:
            self.chat_module.ai = self.ai_engine
        if self.knowledge_module:
            self.knowledge_module.ai = self.ai_engine

        # Очищаем кеш настроек, чтобы пересоздать вид
        self._module_views.pop("settings", None)

        self.page.show_dialog(
            ft.SnackBar(content=ft.Text("Настройки сохранены"), duration=2000)
        )

    def _do_backup(self, e):
        """Создать резервную копию."""
        path = create_backup(self.db.db_path)
        if path:
            self.page.show_dialog(
                ft.SnackBar(content=ft.Text(f"Бэкап создан: {path}"), duration=3000)
            )
        else:
            self.page.show_dialog(
                ft.SnackBar(content=ft.Text("Ошибка создания бэкапа"), duration=3000)
            )

    def _do_export(self, e):
        """Экспортировать данные."""
        path = export_data_to_json(self.db)
        self.page.show_dialog(
            ft.SnackBar(content=ft.Text(f"Данные экспортированы: {path}"), duration=3000)
        )

    def _check_updates(self, e=None):
        """Проверить обновления (по кнопке)."""
        self.page.run_task(self._check_updates_async, show_only_if_available=False)

    def _check_ai_connection(self, e):
        """Проверить подключение к AI."""
        self.page.run_task(self._check_ai_async)

    async def _check_updates_async(self, show_only_if_available: bool = False):
        """Проверить наличие обновлений в Git."""
        try:
            has_updates, current, new_commit = check_for_updates()
            if show_only_if_available and not has_updates:
                return
            if not is_git_repo():
                self.page.show_dialog(
                    ft.SnackBar(content=ft.Text("Проект не в Git-репозитории."), duration=3000)
                )
                return
            if has_updates:
                def on_apply(_e):
                    self.page.pop_dialog()
                    self.page.run_task(self._apply_update_async)

                def on_cancel(_e):
                    self.page.pop_dialog()

                dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Доступно обновление"),
                    content=ft.Text(
                        f"Есть новые изменения в репозитории. "
                        f"Текущий: {current or '—'} → новый: {new_commit or '—'}\n\n"
                        "Применить обновление (git pull)?"
                    ),
                    actions=[
                        ft.TextButton(content=ft.Text("Отмена"), on_click=on_cancel),
                        ft.FilledButton(content=ft.Text("Обновить"), on_click=on_apply),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                self.page.show_dialog(dlg)
            else:
                self.page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("Обновлений нет. У вас последняя версия."),
                        duration=3000,
                    )
                )
        except Exception as ex:
            logger.error(f"Проверка обновлений: {ex}")
            self.page.show_dialog(
                ft.SnackBar(content=ft.Text(f"Ошибка: {ex}"), duration=4000)
            )

    async def _apply_update_async(self):
        """Применить обновление и уведомить пользователя."""
        success, message = apply_update()
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(f"✓ {message}" if success else f"✗ {message}"),
                duration=5000,
            )
        )
        if success:
            # Предложить перезапуск
            def on_restart(_e):
                from utils.updater import restart_app
                restart_app()

            restart_dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Обновление применено"),
                content=ft.Text("Перезапустить приложение для применения изменений?"),
                actions=[
                    ft.TextButton(content=ft.Text("Позже"), on_click=lambda e: self.page.pop_dialog()),
                    ft.FilledButton(content=ft.Text("Перезапустить"), on_click=on_restart),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.show_dialog(restart_dlg)
        self.page.update()

    async def _check_ai_async(self):
        """Асинхронная проверка AI."""
        results = await self.ai_engine.check_providers()
        status_parts = []
        for name, available in results.items():
            status = "доступен" if available else "недоступен"
            status_parts.append(f"{name}: {status}")
        message = " | ".join(status_parts)
        self.page.show_dialog(
            ft.SnackBar(content=ft.Text(f"AI статус: {message}"), duration=4000)
        )

    def _open_ollama_catalog(self, e=None):
        """Открыть каталог моделей Ollama в браузере и скопировать ссылку."""
        url = "https://ollama.com/library"
        try:
            webbrowser.open(url)
            self.page.set_clipboard_text(url)
            self.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text("Ссылка открыта в браузере и скопирована в буфер."),
                    duration=2000,
                )
            )
        except Exception as ex:
            logger.warning(f"Не удалось открыть браузер: {ex}")
            try:
                self.page.set_clipboard_text(url)
                self.page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("Ссылка скопирована в буфер обмена."),
                        duration=2000,
                    )
                )
            except Exception:
                self.page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(f"Ссылка: {url}"),
                        duration=5000,
                    )
                )

    def _download_model(self, e):
        """Запустить загрузку файла модели по ссылке."""
        url = (self.model_url_field.value or "").strip()
        if not url:
            self.page.show_dialog(
                ft.SnackBar(content=ft.Text("Укажите ссылку на файл."), duration=3000)
            )
            return
        self.page.run_task(self._download_model_async, url)

    async def _download_model_async(self, url: str):
        """Асинхронная загрузка файла по ссылке (любой формат: .zip, .gguf, .bin и т.д.)."""
        try:
            import httpx

            models_dir = DATA_DIR / "models"
            models_dir.mkdir(parents=True, exist_ok=True)

            # Извлекаем имя файла из URL (без query-параметров)
            parsed = urlparse(url)
            filename = unquote(parsed.path.split("/")[-1].strip()) or "downloaded_file"
            dest_path = models_dir / filename

            self.model_progress.value = 0
            self.model_progress.visible = True
            self.model_progress.update()

            async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
                async with client.stream("GET", url) as resp:
                    resp.raise_for_status()
                    total = int(resp.headers.get("content-length") or 0)
                    downloaded = 0
                    with open(dest_path, "wb") as f:
                        async for chunk in resp.aiter_bytes(chunk_size=8192):
                            if not chunk:
                                continue
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total:
                                self.model_progress.value = downloaded / total
                                self.model_progress.update()

            self.model_progress.value = 1.0
            self.model_progress.update()

            # Сохраняем путь к модели в конфиг
            self._update_setting("ai.local_model_path", str(dest_path))
            self.config.save()

            self.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"Файл загружен: {dest_path}"),
                    duration=4000,
                )
            )
        except Exception as ex:
            logger.error(f"Ошибка загрузки: {ex}")
            self.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"Ошибка загрузки: {ex}"),
                    duration=4000,
                )
            )
        finally:
            self.page.update()

    def shutdown(self):
        """Завершение работы приложения."""
        logger.info("Завершение Sphere...")
        self.config.save()
        self.db.close()
        logger.info("Sphere завершён")
