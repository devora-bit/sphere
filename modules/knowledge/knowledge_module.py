"""
Sphere — Модуль базы знаний.
"""

import flet as ft
import os
import shutil
from pathlib import Path
from typing import Optional

from core.ai_engine import AIEngine
from core.event_bus import event_bus, Events
from database import Database
from vector_db import VectorDB
from config import KNOWLEDGE_DIR
from ui.layouts.knowledge_layout import KnowledgeLayout
from loguru import logger


class KnowledgeModule:
    """Модуль базы знаний — загрузка и Q&A по документам."""

    def __init__(self, db: Database, vector_db: VectorDB, ai_engine: AIEngine, page: ft.Page):
        self.db = db
        self.vector_db = vector_db
        self.ai = ai_engine
        self.page = page
        self.layout: Optional[KnowledgeLayout] = None

    def build(self) -> KnowledgeLayout:
        """Построить интерфейс базы знаний."""
        self.layout = KnowledgeLayout(
            on_upload=self._on_upload,
            on_ask=self._on_ask,
            on_delete=self._on_delete,
        )
        self._load_documents()
        return self.layout

    def _load_documents(self):
        """Загрузить список документов."""
        if not self.layout:
            return
        docs = self.db.get_documents()
        self.layout.set_documents(docs)

    def _on_upload(self):
        """Открыть диалог загрузки файла."""
        file_picker = ft.FilePicker(on_result=self._on_file_picked)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.pick_files(
            allowed_extensions=["pdf", "docx", "md", "txt", "html"],
            dialog_title="Выберите документ для загрузки",
        )

    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """Обработка выбранного файла."""
        if not e.files:
            return
        for f in e.files:
            try:
                src_path = f.path
                if not src_path:
                    continue
                filename = f.name
                filetype = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

                # Копируем файл в директорию знаний
                KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
                dest_path = KNOWLEDGE_DIR / filename
                shutil.copy2(src_path, dest_path)

                # Добавляем в БД
                doc_id = self.db.add_document(
                    filename=filename,
                    filepath=str(dest_path),
                    filetype=filetype,
                    title=filename.rsplit(".", 1)[0],
                )

                # Обрабатываем документ
                self.page.run_task(self._process_document, doc_id, str(dest_path), filetype)

                logger.info(f"Документ загружен: {filename}")
                event_bus.emit(Events.DOCUMENT_ADDED, {"id": doc_id, "filename": filename})

            except Exception as ex:
                logger.error(f"Ошибка загрузки файла: {ex}")

        self._load_documents()
        self.page.update()

    async def _process_document(self, doc_id: int, filepath: str, filetype: str):
        """Обработать документ — извлечь текст и создать эмбеддинги."""
        try:
            text = self._extract_text(filepath, filetype)
            if not text:
                return

            # Разбиваем на чанки
            chunks = self._split_text(text, chunk_size=500, overlap=50)

            # Добавляем в векторную базу
            if self.vector_db.is_available:
                ids = [f"doc_{doc_id}_chunk_{i}" for i in range(len(chunks))]
                metadatas = [{"doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]
                self.vector_db.add_texts(chunks, metadatas=metadatas, ids=ids)

            # Генерируем краткое содержание
            summary = text[:500] + "..." if len(text) > 500 else text

            # Обновляем БД
            self.db.update_document(
                doc_id,
                processed=True,
                chunk_count=len(chunks),
                summary=summary,
            )

            self._load_documents()
            self.layout.update()
            event_bus.emit(Events.DOCUMENT_PROCESSED, {"id": doc_id})

        except Exception as e:
            logger.error(f"Ошибка обработки документа: {e}")

    def _extract_text(self, filepath: str, filetype: str) -> str:
        """Извлечь текст из документа."""
        try:
            if filetype in ("txt", "md"):
                with open(filepath, "r", encoding="utf-8") as f:
                    return f.read()
            elif filetype == "pdf":
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(filepath)
                    return "\n".join(page.extract_text() or "" for page in reader.pages)
                except ImportError:
                    logger.warning("PyPDF2 не установлен")
                    return ""
            elif filetype == "docx":
                try:
                    from docx import Document
                    doc = Document(filepath)
                    return "\n".join(p.text for p in doc.paragraphs)
                except ImportError:
                    logger.warning("python-docx не установлен")
                    return ""
            elif filetype == "html":
                try:
                    from bs4 import BeautifulSoup
                    with open(filepath, "r", encoding="utf-8") as f:
                        soup = BeautifulSoup(f.read(), "html.parser")
                    return soup.get_text()
                except ImportError:
                    logger.warning("beautifulsoup4 не установлен")
                    return ""
        except Exception as e:
            logger.error(f"Ошибка извлечения текста: {e}")
        return ""

    def _split_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list:
        """Разбить текст на чанки с перекрытием."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start = end - overlap
        return chunks if chunks else [text]

    def _on_ask(self, question: str):
        """Задать вопрос по документам."""
        if not self.layout:
            return
        self.layout.set_answer("*Ищу ответ...*")
        self.layout.update()
        self.page.run_task(self._answer_question, question)

    async def _answer_question(self, question: str):
        """Ответить на вопрос используя RAG."""
        try:
            # Ищем релевантные фрагменты
            results = self.vector_db.search(question, n_results=3)
            if not results:
                self.layout.set_answer("Не найдено релевантных документов. Загрузите документы для начала работы.")
                self.layout.update()
                return

            # Формируем контекст
            context_parts = [r["document"] for r in results]
            context = "\n\n---\n\n".join(context_parts)

            # Формируем промпт для ИИ
            prompt = (
                f"На основе следующих фрагментов документов ответь на вопрос пользователя.\n\n"
                f"Фрагменты:\n{context}\n\n"
                f"Вопрос: {question}\n\n"
                f"Ответ (используй Markdown):"
            )

            response = await self.ai.chat(prompt)
            self.layout.set_answer(response)
            self.layout.update()

        except Exception as e:
            logger.error(f"Ошибка RAG: {e}")
            self.layout.set_answer(f"Ошибка: {e}")
            self.layout.update()

    def _on_delete(self, doc_id: int):
        """Удалить документ."""
        # Удаляем чанки из векторной базы
        try:
            doc = None
            for d in self.db.get_documents():
                if d["id"] == doc_id:
                    doc = d
                    break
            if doc:
                chunk_count = doc.get("chunk_count", 0)
                if chunk_count and self.vector_db.is_available:
                    ids = [f"doc_{doc_id}_chunk_{i}" for i in range(chunk_count)]
                    self.vector_db.delete(ids)
                # Удаляем файл
                filepath = doc.get("filepath", "")
                if filepath and os.path.exists(filepath):
                    os.remove(filepath)
        except Exception as e:
            logger.error(f"Ошибка удаления документа: {e}")

        # Удаляем из БД (простой DELETE)
        conn = self.db.connect()
        conn.execute("DELETE FROM knowledge_documents WHERE id = ?", (doc_id,))
        conn.commit()

        self._load_documents()
        self.page.update()
