"""
Sphere — Тёмная тема.
"""

import flet as ft


def get_dark_theme() -> ft.Theme:
    """Создать тёмную тему для Sphere."""
    return ft.Theme(
        color_scheme_seed="#626880",
        color_scheme=ft.ColorScheme(
            primary="#626880",
            on_primary=ft.Colors.WHITE,
            primary_container="#4D5466",
            on_primary_container="#E6EDF3",
            secondary="#7A8199",
            on_secondary=ft.Colors.BLACK,
            secondary_container="#626880",
            on_secondary_container="#E6EDF3",
            tertiary=ft.Colors.PURPLE_200,
            on_tertiary=ft.Colors.BLACK,
            tertiary_container=ft.Colors.PURPLE_900,
            on_tertiary_container=ft.Colors.PURPLE_100,
            surface=ft.Colors.with_opacity(1.0, "#161B22"),
            on_surface=ft.Colors.with_opacity(1.0, "#E6EDF3"),
            surface_container=ft.Colors.with_opacity(1.0, "#1C2128"),
            surface_container_low=ft.Colors.with_opacity(1.0, "#21262D"),
            surface_container_high=ft.Colors.with_opacity(1.0, "#30363D"),
            outline=ft.Colors.with_opacity(1.0, "#8B949E"),
            outline_variant=ft.Colors.with_opacity(0.5, "#8B949E"),
            on_surface_variant=ft.Colors.with_opacity(0.9, "#E6EDF3"),
        ),
        use_material3=True,
        visual_density=ft.VisualDensity.COMFORTABLE,
        text_theme=ft.TextTheme(
            body_large=ft.TextStyle(size=15),
            body_medium=ft.TextStyle(size=14),
            body_small=ft.TextStyle(size=12),
            title_large=ft.TextStyle(size=22, weight=ft.FontWeight.W_600),
            title_medium=ft.TextStyle(size=18, weight=ft.FontWeight.W_500),
        ),
    )
