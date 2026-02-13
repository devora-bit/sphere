"""
Sphere — Конфигурация и настройки приложения.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Корневая директория проекта
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

# Директории данных
DB_PATH = DATA_DIR / "sphere.db"
CHROMA_DIR = DATA_DIR / "chroma"
NOTES_DIR = DATA_DIR / "notes"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
EXPORTS_DIR = DATA_DIR / "exports"
BACKUPS_DIR = DATA_DIR / "backups"

CONFIG_FILE = DATA_DIR / "config.yaml"


@dataclass
class AIConfig:
    """Настройки ИИ-провайдеров."""

    # Текущий провайдер: ollama / deepseek / local
    provider: str = "ollama"

    # Ollama (локальные модели)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama2"

    # DeepSeek R1 (OpenAI‑совместимый API)
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-r1"
    deepseek_base_url: str = "https://api.deepseek.com"

    # Локальный файл модели, скачанный по ссылке
    local_model_path: Optional[str] = None
    local_model_url: Optional[str] = None

    # Общие параметры
    embedding_model: str = "all-MiniLM-L6-v2"
    max_context_length: int = 4096
    temperature: float = 0.7

    # Режим общения с ИИ: только база знаний / гибрид / только модель
    search_mode: str = "hybrid"  # knowledge | hybrid | model_only

    # Отображаемое имя ИИ-агента (если пусто — по умолчанию из провайдера/модели)
    ai_agent_name: Optional[str] = None


@dataclass
class UIConfig:
    """Настройки интерфейса."""
    theme_mode: str = "dark"  # dark / light / system
    color_seed: str = "indigo"
    language: str = "ru"
    window_width: int = 1200
    window_height: int = 800
    sidebar_extended: bool = True


@dataclass
class TelegramConfig:
    """Настройки Telegram бота (уведомления + выгрузка/восстановление бекапа)."""
    enabled: bool = False
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    # file_id последнего бекапа, отправленного в Telegram (для «достать бекап»)
    last_backup_file_id: Optional[str] = None
    last_backup_sent_at: Optional[str] = None


@dataclass
class AppConfig:
    """Главная конфигурация приложения."""
    ai: AIConfig = field(default_factory=AIConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    auto_backup: bool = True
    backup_interval_hours: int = 24
    auto_update_on_start: bool = False

    def save(self):
        """Сохранить конфигурацию в YAML файл."""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "ai": {
                "provider": self.ai.provider,
                "ollama_host": self.ai.ollama_host,
                "ollama_model": self.ai.ollama_model,
                "deepseek_api_key": self.ai.deepseek_api_key,
                "deepseek_model": self.ai.deepseek_model,
                "deepseek_base_url": self.ai.deepseek_base_url,
                "local_model_path": self.ai.local_model_path,
                "local_model_url": self.ai.local_model_url,
                "embedding_model": self.ai.embedding_model,
                "max_context_length": self.ai.max_context_length,
                "temperature": self.ai.temperature,
                "search_mode": self.ai.search_mode,
                "ai_agent_name": self.ai.ai_agent_name,
            },
            "ui": {
                "theme_mode": self.ui.theme_mode,
                "color_seed": self.ui.color_seed,
                "language": self.ui.language,
                "window_width": self.ui.window_width,
                "window_height": self.ui.window_height,
                "sidebar_extended": self.ui.sidebar_extended,
            },
            "telegram": {
                "enabled": self.telegram.enabled,
                "bot_token": self.telegram.bot_token,
                "chat_id": self.telegram.chat_id,
                "last_backup_file_id": self.telegram.last_backup_file_id,
                "last_backup_sent_at": self.telegram.last_backup_sent_at,
            },
            "auto_backup": self.auto_backup,
            "backup_interval_hours": self.backup_interval_hours,
            "auto_update_on_start": self.auto_update_on_start,
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    @classmethod
    def load(cls) -> "AppConfig":
        """Загрузить конфигурацию из YAML файла."""
        if not CONFIG_FILE.exists():
            config = cls()
            config.save()
            return config

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        ai_data = data.get("ai", {})
        # Удаляем OpenAI — только локальные/альтернативные провайдеры
        ai_data = {k: v for k, v in ai_data.items() if k not in ("openai_api_key", "openai_model")}
        if ai_data.get("provider") == "openai":
            ai_data["provider"] = "ollama"
        # Миграция search_mode: local->knowledge, web->model_only
        sm = ai_data.get("search_mode", "hybrid")
        if sm == "local":
            ai_data["search_mode"] = "knowledge"
        elif sm == "web":
            ai_data["search_mode"] = "model_only"
        ui_data = data.get("ui", {})
        tg_data = data.get("telegram", {})

        return cls(
            ai=AIConfig(**{k: v for k, v in ai_data.items() if v is not None}),
            ui=UIConfig(**{k: v for k, v in ui_data.items() if v is not None}),
            telegram=TelegramConfig(**{k: v for k, v in tg_data.items() if v is not None}),
            auto_backup=data.get("auto_backup", True),
            backup_interval_hours=data.get("backup_interval_hours", 24),
            auto_update_on_start=data.get("auto_update_on_start", False),
        )


def ensure_directories():
    """Создать все необходимые директории."""
    for d in [DATA_DIR, CHROMA_DIR, NOTES_DIR, KNOWLEDGE_DIR, EXPORTS_DIR, BACKUPS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
