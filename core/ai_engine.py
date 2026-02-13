"""
Sphere — Ядро ИИ с поддержкой нескольких провайдеров.
"""

import asyncio
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from abc import ABC, abstractmethod
from loguru import logger

from config import AppConfig


class AIProvider(ABC):
    """Абстрактный провайдер ИИ."""

    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        pass

    @abstractmethod
    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        pass


class OllamaProvider(AIProvider):
    """Провайдер через Ollama (локальные модели)."""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama2"):
        self.host = host
        self.model = model

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        try:
            import ollama
            client = ollama.AsyncClient(host=self.host)
            response = await client.chat(
                model=kwargs.get("model", self.model),
                messages=messages,
            )
            return response["message"]["content"]
        except ImportError:
            logger.error("Библиотека ollama не установлена")
            return "Ошибка: библиотека ollama не установлена. Выполните: pip install ollama"
        except Exception as e:
            logger.error(f"Ошибка Ollama: {e}")
            return f"Ошибка подключения к Ollama: {e}"

    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        try:
            import ollama
            client = ollama.AsyncClient(host=self.host)
            stream = await client.chat(
                model=kwargs.get("model", self.model),
                messages=messages,
                stream=True,
            )
            async for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
        except ImportError:
            yield "Ошибка: библиотека ollama не установлена."
        except Exception as e:
            yield f"Ошибка: {e}"

    async def is_available(self) -> bool:
        try:
            import ollama
            client = ollama.AsyncClient(host=self.host)
            await client.list()
            return True
        except Exception:
            return False


class DeepSeekProvider(AIProvider):
    """Провайдер через DeepSeek (OpenAI‑совместимый API)."""

    def __init__(self, api_key: str | None, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/") if base_url else ""

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        if not self.api_key:
            return "Ошибка: DeepSeek API ключ не настроен. Укажите его в настройках."
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url or None)
            response = await client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
            )
            return response.choices[0].message.content
        except ImportError:
            return "Ошибка: библиотека openai не установлена."
        except Exception as e:
            logger.error(f"Ошибка DeepSeek: {e}")
            return f"Ошибка DeepSeek: {e}"

    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        if not self.api_key:
            yield "Ошибка: DeepSeek API ключ не настроен."
            return
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url or None)
            stream = await client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except ImportError:
            yield "Ошибка: библиотека openai не установлена."
        except Exception as e:
            yield f"Ошибка DeepSeek: {e}"

    async def is_available(self) -> bool:
        return self.api_key is not None


class AIEngine:
    """Ядро ИИ — управляет провайдерами и историей."""

    SYSTEM_PROMPT = (
        "Ты — Sphere AI Assistant, локальный помощник с доступом к данным пользователя. "
        "Тебе передаются релевантные заметки, задачи и фрагменты документов — подбираются по запросу. "
        "Отвечай точно на основе этих данных: цитируй, ссылайся на конкретные записи, делай выводы. "
        "С пользователем можно говорить о чём угодно — о его заметках, планах, документах; твои ответы опираются на его же данные. "
        "Отвечай кратко и по делу. Используй Markdown для форматирования."
    )

    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        self.providers: Dict[str, AIProvider] = {}
        self.conversation_history: List[Dict] = []
        self._setup_providers()

    def _setup_providers(self):
        """Настроить доступных провайдеров."""
        self.providers["ollama"] = OllamaProvider(
            host=self.config.ai.ollama_host,
            model=self.config.ai.ollama_model,
        )
        if self.config.ai.deepseek_api_key:
            self.providers["deepseek"] = DeepSeekProvider(
                api_key=self.config.ai.deepseek_api_key,
                model=self.config.ai.deepseek_model,
                base_url=self.config.ai.deepseek_base_url,
            )

    @property
    def current_provider(self) -> str:
        return self.config.ai.provider

    @current_provider.setter
    def current_provider(self, value: str):
        if value in self.providers:
            self.config.ai.provider = value

    def get_provider(self) -> AIProvider:
        provider = self.providers.get(self.current_provider)
        if not provider:
            # Fallback к первому доступному
            for name, p in self.providers.items():
                return p
        return provider

    def _build_messages(self, user_message: str, context: Dict = None, mode: str = "hybrid") -> List[Dict]:
        """Собрать список сообщений для отправки в модель."""
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        # Добавляем контекст если есть
        if context:
            context_text = self._format_context(context)
            if context_text:
                ctx_msg = f"Контекст пользователя:\n{context_text}"
                if mode == "knowledge":
                    ctx_msg += "\n\nВАЖНО: Отвечай ТОЛЬКО на основе данных из контекста выше. Не используй свои общие знания. Если информации нет в контексте — так и скажи."
                messages.append({"role": "system", "content": ctx_msg})

        # Добавляем историю (последние N сообщений)
        max_history = 20
        for msg in self.conversation_history[-max_history:]:
            messages.append(msg)

        # Добавляем текущее сообщение
        messages.append({"role": "user", "content": user_message})
        return messages

    def _format_context(self, context: Dict) -> str:
        """Форматировать контекст из других модулей и поиска по данным пользователя."""
        parts = []
        if "tasks" in context:
            tasks = context["tasks"]
            if tasks:
                parts.append("Текущие задачи: " + ", ".join(t.get("title", "") for t in tasks[:5]))
        if "events" in context:
            events = context["events"]
            if events:
                parts.append("Ближайшие события: " + ", ".join(e.get("title", "") for e in events[:5]))
        if "notes" in context:
            notes = context["notes"]
            if notes:
                parts.append("Последние заметки: " + ", ".join(n.get("title", "") for n in notes[:5]))

        # Результаты поиска по данным пользователя (заметки, задачи, документы)
        if "search_notes" in context and context["search_notes"]:
            items = []
            for n in context["search_notes"][:5]:
                title = n.get("title", "")
                content = (n.get("content", "") or "")[:200]
                if content:
                    items.append(f"«{title}»: {content}...")
                else:
                    items.append(title)
            parts.append("Релевантные заметки:\n" + "\n".join(items))
        if "search_tasks" in context and context["search_tasks"]:
            items = [f"- {t.get('title', '')}: {t.get('description', '')[:150]}" for t in context["search_tasks"][:5]]
            parts.append("Релевантные задачи:\n" + "\n".join(items))
        if "search_docs" in context and context["search_docs"]:
            items = [f"- {d.get('document', '')[:300]}..." for d in context["search_docs"][:5]]
            parts.append("Релевантные фрагменты из документов:\n" + "\n".join(items))

        return "\n\n".join(parts) if parts else ""

    async def chat(self, message: str, context: Dict = None, mode: str = "hybrid") -> str:
        """Основной метод чата — получить полный ответ."""
        messages = self._build_messages(message, context, mode)
        provider = self.get_provider()
        if not provider:
            return "Ошибка: нет доступных ИИ-провайдеров. Проверьте настройки."

        response = await provider.chat(messages)

        # Сохраняем в историю
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    async def chat_stream(self, message: str, context: Dict = None, mode: str = "hybrid") -> AsyncGenerator[str, None]:
        """Стриминг ответа по частям."""
        messages = self._build_messages(message, context, mode)
        provider = self.get_provider()
        if not provider:
            yield "Ошибка: нет доступных ИИ-провайдеров."
            return

        full_response = ""
        async for chunk in provider.chat_stream(messages):
            full_response += chunk
            yield chunk

        # Сохраняем в историю
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": full_response})

    def clear_history(self):
        """Очистить историю разговора."""
        self.conversation_history.clear()

    def load_history(self, messages: List[Dict]):
        """Загрузить историю из базы данных."""
        self.conversation_history = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]

    async def check_providers(self) -> Dict[str, bool]:
        """Проверить доступность провайдеров."""
        result = {}
        for name, provider in self.providers.items():
            result[name] = await provider.is_available()
        return result
