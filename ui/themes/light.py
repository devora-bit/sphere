"""
Sphere — Светлая тема.
"""

import flet as ft


def get_light_theme() -> ft.Theme:
    """Создать светлую тему для Sphere."""
    return ft.Theme(
        color_scheme_seed="#C6D0F5",
        color_scheme=ft.ColorScheme(
            primary="#C6D0F5",
            on_primary="#24292F",
            primary_container="#A8B3E8",
            on_primary_container="#24292F",
            secondary="#D8DFF7",
            on_secondary="#24292F",
            secondary_container="#C6D0F5",
            on_secondary_container="#24292F",
            tertiary=ft.Colors.PURPLE_700,
            on_tertiary=ft.Colors.WHITE,
            tertiary_container=ft.Colors.PURPLE_200,
            on_tertiary_container=ft.Colors.with_opacity(1.0, "#24292F"),
            surface=ft.Colors.WHITE,
            on_surface=ft.Colors.with_opacity(1.0, "#24292F"),
            surface_container=ft.Colors.with_opacity(1.0, "#F6F8FA"),
            surface_container_low=ft.Colors.with_opacity(1.0, "#FAFBFC"),
            surface_container_high=ft.Colors.with_opacity(1.0, "#D0D7DE"),
            outline=ft.Colors.with_opacity(1.0, "#57606A"),
            outline_variant=ft.Colors.with_opacity(0.5, "#57606A"),
            on_surface_variant=ft.Colors.with_opacity(0.8, "#24292F"),
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
