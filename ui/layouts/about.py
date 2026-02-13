"""
Sphere — Страница «О проекте».
"""

import flet as ft
from pathlib import Path


class AboutLayout(ft.Column):
    """Страница 'О проекте Sphere' с автором и DEVLOG."""

    def __init__(self, version: str = "", **kwargs):
        super().__init__(spacing=0, expand=True, **kwargs)

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=22, color=ft.Colors.ON_SURFACE),
                    ft.Text("О проекте Sphere", size=18, weight=ft.FontWeight.W_600),
                    ft.Text(f" · {version}", size=14, color=ft.Colors.OUTLINE) if version else ft.Container(),
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )

        author_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Автор", size=16, weight=ft.FontWeight.W_600),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.SEND, size=16),
                            ft.Text("Telegram: @losstq", size=13),
                        ],
                        spacing=6,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.all(16),
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
            margin=ft.margin.symmetric(horizontal=16, vertical=8),
        )

        devlog_text = "*Файл DEVLOG.md не найден.*"
        devlog_path = Path("DEVLOG.md")
        if devlog_path.exists():
            try:
                devlog_text = devlog_path.read_text(encoding="utf-8")
            except Exception:
                pass

        devlog_block = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Dev Log", size=16, weight=ft.FontWeight.W_600),
                    ft.Divider(height=8, thickness=0.5),
                    ft.Markdown(
                        devlog_text,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        selectable=True,
                        expand=True,
                    ),
                ],
                spacing=8,
                expand=True,
            ),
            padding=ft.padding.all(16),
            margin=ft.margin.symmetric(horizontal=16, vertical=8),
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
            expand=True,
        )

        self.controls = [
            header,
            ft.Divider(height=1, thickness=0.5),
            author_card,
            devlog_block,
        ]
        self.scroll = ft.ScrollMode.AUTO

