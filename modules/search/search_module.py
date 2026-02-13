"""
Sphere — Модуль нейронного поиска.
"""

import flet as ft
from typing import Optional, List, Dict

from database import Database
from vector_db import VectorDB
from loguru import logger


class SearchModule:
    """Модуль единого поиска по всем данным."""

    def __init__(self, db: Database, vector_db: VectorDB, page: ft.Page):
        self.db = db
        self.vector_db = vector_db
        self.page = page

    def build(self) -> ft.Column:
        """Построить интерфейс поиска."""
        # Поле поиска
        self.search_field = ft.TextField(
            hint_text="Введите поисковый запрос...",
            expand=True,
            border_radius=24,
            filled=True,
            text_size=16,
            prefix_icon=ft.Icons.SEARCH,
            content_padding=ft.padding.only(left=20, right=16, top=12, bottom=12),
            autofocus=True,
            on_submit=self._on_search,
        )

        search_btn = ft.FilledButton(
            content=ft.Text("Найти"),
            on_click=self._on_search,
            height=44,
        )

        # Фильтры
        self.filter_chips = ft.Row(
            [
                ft.Chip(label=ft.Text("Все"), selected=True, on_select=lambda e: self._set_filter("all")),
                ft.Chip(label=ft.Text("Заметки"), on_select=lambda e: self._set_filter("notes")),
                ft.Chip(label=ft.Text("Задачи"), on_select=lambda e: self._set_filter("tasks")),
                ft.Chip(label=ft.Text("Документы"), on_select=lambda e: self._set_filter("knowledge")),
            ],
            spacing=8,
        )

        self.current_filter = "all"

        # Результаты
        self.results_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.padding.symmetric(horizontal=24, vertical=8),
        )

        self.results_count = ft.Text(
            "",
            size=13,
            color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
        )

        # Начальное состояние
        self.results_list.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.SEARCH, size=64, color=ft.Colors.with_opacity(0.15, ft.Colors.ON_SURFACE)),
                        ft.Text(
                            "Введите запрос для поиска",
                            size=16,
                            color=ft.Colors.with_opacity(0.4, ft.Colors.ON_SURFACE),
                        ),
                        ft.Text(
                            "Поиск работает по заметкам, задачам и документам",
                            size=13,
                            color=ft.Colors.with_opacity(0.3, ft.Colors.ON_SURFACE),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                alignment=ft.Alignment.CENTER,
                padding=ft.padding.all(60),
            )
        )

        return ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.SEARCH, color=ft.Colors.ON_SURFACE, size=20),
                                        ft.Text("Поиск", size=16, weight=ft.FontWeight.W_600),
                                    ],
                                    spacing=8,
                                ),
                                padding=ft.padding.symmetric(horizontal=24, vertical=8),
                            ),
                            ft.Container(
                                content=ft.Row([self.search_field, search_btn], spacing=12),
                                padding=ft.padding.symmetric(horizontal=24, vertical=8),
                            ),
                            ft.Container(
                                content=ft.Row([self.filter_chips, ft.Container(expand=True), self.results_count]),
                                padding=ft.padding.symmetric(horizontal=24),
                            ),
                        ],
                        spacing=0,
                    ),
                ),
                ft.Divider(height=1, thickness=0.5),
                self.results_list,
            ],
            spacing=0,
            expand=True,
        )

    def _set_filter(self, filter_type: str):
        self.current_filter = filter_type
        # Если уже есть запрос, повторяем поиск
        if self.search_field.value:
            self._on_search(None)

    def _on_search(self, e):
        """Выполнить поиск."""
        query = self.search_field.value
        if not query or not query.strip():
            return

        query = query.strip()
        self.results_list.controls.clear()
        results = []

        # Текстовый поиск по БД
        if self.current_filter in ("all", "notes"):
            notes = self.db.search_notes(query)
            for n in notes:
                results.append(self._result_card(
                    title=n["title"],
                    snippet=(n.get("content", "") or "")[:100],
                    category="Заметка",
                    icon=ft.Icons.EDIT_NOTE,
                    color=ft.Colors.PRIMARY,
                ))

        if self.current_filter in ("all", "tasks"):
            tasks = self.db.search_tasks(query)
            for t in tasks:
                results.append(self._result_card(
                    title=t["title"],
                    snippet=t.get("description", "") or t.get("status", ""),
                    category="Задача",
                    icon=ft.Icons.TASK_ALT,
                    color=ft.Colors.AMBER,
                ))

        # Векторный поиск
        if self.current_filter in ("all", "knowledge") and self.vector_db.is_available:
            vector_results = self.vector_db.search(query, n_results=5)
            for vr in vector_results:
                results.append(self._result_card(
                    title=f"Документ #{vr.get('metadata', {}).get('doc_id', '?')}",
                    snippet=vr.get("document", "")[:120],
                    category="Документ",
                    icon=ft.Icons.SCHOOL,
                    color=ft.Colors.TERTIARY,
                    distance=vr.get("distance", 0),
                ))

        if not results:
            self.results_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Ничего не найдено",
                        size=14,
                        color=ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE),
                    ),
                    padding=ft.padding.all(40),
                    alignment=ft.Alignment.CENTER,
                )
            )

        for r in results:
            self.results_list.controls.append(r)

        self.results_count.value = f"Найдено: {len(results)}"
        self.page.update()

    def _result_card(self, title: str, snippet: str, category: str,
                     icon, color, distance: float = None) -> ft.Container:
        """Карточка результата поиска."""
        subtitle_parts = [category]
        if distance is not None:
            subtitle_parts.append(f"Релевантность: {1 - distance:.0%}")

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, color=color, size=20),
                    ft.Column(
                        [
                            ft.Text(title, size=14, weight=ft.FontWeight.W_500),
                            ft.Text(
                                snippet,
                                size=12,
                                color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                " • ".join(subtitle_parts),
                                size=11,
                                color=color,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.padding.all(12),
            border_radius=8,
            border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE)),
            ink=True,
        )

    def search_global(self, query: str):
        """Выполнить поиск (вызывается из хедера)."""
        self.search_field.value = query
        self._on_search(None)
