"""
Sphere — Инициализация и управление ChromaDB (векторная база данных).
"""

import warnings
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger

from config import CHROMA_DIR


class VectorDB:
    """Обёртка над ChromaDB для семантического поиска."""

    def __init__(self, persist_dir: Path = CHROMA_DIR):
        self.persist_dir = persist_dir
        self._client = None
        self._collection = None

    def initialize(self):
        """Инициализировать ChromaDB."""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                import chromadb

            self.persist_dir.mkdir(parents=True, exist_ok=True)
            # Без Settings — обход несовместимости ChromaDB с Python 3.14 (Pydantic v1)
            self._client = chromadb.PersistentClient(path=str(self.persist_dir))
            self._collection = self._client.get_or_create_collection(
                name="sphere_main",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB инициализирована: {self.persist_dir}")
        except ImportError:
            logger.warning("ChromaDB не установлена. Векторный поиск недоступен.")
        except Exception as e:
            logger.warning(
                f"ChromaDB недоступна (Python 3.14?): {e}. "
                "Векторный поиск отключён. Используйте Python 3.12/3.13 для полной поддержки."
            )
            self._client = None
            self._collection = None

    @property
    def is_available(self) -> bool:
        return self._collection is not None

    def add_texts(self, texts: List[str], metadatas: List[Dict] = None,
                  ids: List[str] = None):
        """Добавить тексты в векторную базу."""
        if not self.is_available:
            return
        if not ids:
            existing = self._collection.count()
            ids = [f"doc_{existing + i}" for i in range(len(texts))]
        self._collection.add(
            documents=texts,
            metadatas=metadatas or [{}] * len(texts),
            ids=ids,
        )
        logger.debug(f"Добавлено {len(texts)} документов в ChromaDB")

    def search(self, query: str, n_results: int = 5,
               where: Dict = None) -> List[Dict]:
        """Семантический поиск по векторной базе."""
        if not self.is_available:
            return []
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
            )
            output = []
            for i in range(len(results["ids"][0])):
                output.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
            return output
        except Exception as e:
            logger.error(f"Ошибка поиска в ChromaDB: {e}")
            return []

    def delete(self, ids: List[str]):
        """Удалить документы по ID."""
        if not self.is_available:
            return
        self._collection.delete(ids=ids)

    def count(self) -> int:
        """Количество документов в базе."""
        if not self.is_available:
            return 0
        return self._collection.count()


# Глобальный экземпляр
vector_db = VectorDB()
