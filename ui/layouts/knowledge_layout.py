"""
Sphere — Макет базы знаний.
"""

import flet as ft
from typing import Callable, List, Dict


class KnowledgeLayout(ft.Column):
    """Макет страницы базы знаний."""

    def __init__(
        self,
        on_upload: Callable = None,
        on_ask: Callable = None,
        on_delete: Callable = None,
        **kwargs,
    ):
        self._on_upload = on_upload
        self._on_ask = on_ask
        self._on_delete = on_delete

        # Заголовок
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.SCHOOL, color=ft.Colors.ON_SURFACE, size=20),
                    ft.Text("База знаний", size=16, weight=ft.FontWeight.W_600),
                    ft.Container(expand=True),
                    ft.FilledButton(
                        content=ft.Text("Загрузить документ"),
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=self._handle_upload,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )

        # Поле вопроса по документам
        self.question_field = ft.TextField(
            hint_text="Задайте вопрос по загруженным документам...",
            expand=True,
            border_radius=20,
            filled=True,
            text_size=14,
            prefix_icon=ft.Icons.QUESTION_ANSWER,
            content_padding=ft.padding.only(left=16, right=8, top=10, bottom=10),
            on_submit=self._handle_ask,
        )

        ask_btn = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            on_click=self._handle_ask,
            icon_color=ft.Colors.ON_SURFACE,
        )

        question_bar = ft.Container(
            content=ft.Row([self.question_field, ask_btn], spacing=8),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )

        # Ответ ИИ
        self.answer_area = ft.Container(
            content=ft.Markdown(
                "*Загрузите документы и задайте вопрос, чтобы получить ответ на основе ваших данных.*",
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            ),
            padding=ft.padding.all(16),
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
            margin=ft.margin.symmetric(horizontal=16),
        )

        # Список документов
        self.documents_list = ft.ListView(
            expand=True,
            spacing=4,
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )

        # Статистика
        self.stats_text = ft.Text(
            "Документов: 0 | Фрагментов: 0",
            size=12,
            color=ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE),
        )

        super().__init__(
            controls=[
                header,
                ft.Divider(height=1, thickness=0.5),
                question_bar,
                self.answer_area,
                ft.Divider(height=16, thickness=0),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("Загруженные документы", size=14, weight=ft.FontWeight.W_500),
                            ft.Container(expand=True),
                            self.stats_text,
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=16),
                ),
                self.documents_list,
            ],
            spacing=0,
            expand=True,
            **kwargs,
        )

    def set_documents(self, documents: List[Dict]):
        """Обновить список документов."""
        self.documents_list.controls.clear()
        for doc in documents:
            self.documents_list.controls.append(
                self._document_card(doc)
            )
        total_chunks = sum(d.get("chunk_count", 0) for d in documents)
        self.stats_text.value = f"Документов: {len(documents)} | Фрагментов: {total_chunks}"

    def set_answer(self, text: str):
        """Установить ответ ИИ."""
        self.answer_area.content.value = text

    def _document_card(self, doc: dict) -> ft.Container:
        filetype = doc.get("filetype", "")
        icon_map = {
            "pdf": ft.Icons.PICTURE_AS_PDF,
            "docx": ft.Icons.DESCRIPTION,
            "md": ft.Icons.ARTICLE,
            "html": ft.Icons.WEB,
            "txt": ft.Icons.TEXT_SNIPPET,
        }
        icon = icon_map.get(filetype, ft.Icons.INSERT_DRIVE_FILE)
        processed = doc.get("processed", False)

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=20, color=ft.Colors.ON_SURFACE),
                    ft.Column(
                        [
                            ft.Text(doc.get("title", doc.get("filename", "")), size=14, weight=ft.FontWeight.W_500),
                            ft.Text(
                                f"{filetype.upper()} • {doc.get('chunk_count', 0)} фрагментов"
                                + (" • Обработан" if processed else " • Ожидает обработки"),
                                size=11,
                                color=ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE),
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_size=16,
                        tooltip="Удалить",
                        on_click=lambda e, d=doc: self._handle_delete(d.get("id")),
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.all(10),
            border_radius=8,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)),
        )

    def _handle_upload(self, e):
        if self._on_upload:
            self._on_upload()

    def _handle_ask(self, e):
        question = self.question_field.value
        if question and question.strip() and self._on_ask:
            self._on_ask(question.strip())

    def _handle_delete(self, doc_id):
        if self._on_delete and doc_id:
            self._on_delete(doc_id)
