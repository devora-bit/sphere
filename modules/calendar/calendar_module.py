"""
Sphere — Модуль календаря.
"""

import flet as ft
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict

from core.event_bus import event_bus, Events
from database import Database
from loguru import logger


class CalendarModule:
    """Модуль управления календарём и событиями."""

    def __init__(self, db: Database, page: ft.Page):
        self.db = db
        self.page = page
        self.current_date = date.today()
        self.view_mode = "list"  # list / month

    def build(self) -> ft.Column:
        """Построить интерфейс календаря."""
        # Заголовок
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CALENDAR_TODAY, color=ft.Colors.ON_SURFACE, size=20),
                    ft.Text("Календарь", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                    ft.Container(expand=True),
                    ft.SegmentedButton(
                        segments=[
                            ft.Segment(value="list", label=ft.Text("Список")),
                            ft.Segment(value="month", label=ft.Text("Месяц")),
                        ],
                        selected=["list"],
                        on_change=self._on_view_change,
                    ),
                    ft.Container(width=8),
                    ft.FilledButton(
                        content=ft.Text("Новое событие"),
                        icon=ft.Icons.ADD,
                        on_click=self._show_create_dialog,
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )

        # Навигация по датам
        self.date_label = ft.Text(
            self._format_month(self.current_date),
            size=16,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.ON_SURFACE,
        )

        date_nav = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=self._prev_month, icon_size=18),
                    self.date_label,
                    ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=self._next_month, icon_size=18),
                    ft.Container(expand=True),
                    ft.TextButton(content=ft.Text("Сегодня"), on_click=self._go_today),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=4),
        )

        # Список событий
        self.events_list = ft.ListView(
            expand=True,
            spacing=4,
            padding=ft.padding.all(16),
        )

        self._load_events()

        return ft.Column(
            [
                header,
                ft.Divider(height=1, thickness=0.5),
                date_nav,
                self.events_list,
            ],
            spacing=0,
            expand=True,
        )

    def _load_events(self):
        """Загрузить события за текущий месяц."""
        first_day = self.current_date.replace(day=1)
        if self.current_date.month == 12:
            last_day = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1)
        else:
            last_day = self.current_date.replace(month=self.current_date.month + 1, day=1)

        events = self.db.get_events(
            start_from=first_day.isoformat(),
            start_to=last_day.isoformat(),
        )

        self.events_list.controls.clear()

        if not events:
            self.events_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.EVENT_AVAILABLE, size=48, color=ft.Colors.with_opacity(0.3, ft.Colors.ON_SURFACE)),
                            ft.Text(
                                "Нет событий в этом месяце",
                                size=14,
                                color=ft.Colors.ON_SURFACE,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=ft.padding.all(40),
                )
            )
            return

        # Группируем по дням
        days = {}
        for ev in events:
            day_str = str(ev.get("start_time", ""))[:10]
            if day_str not in days:
                days[day_str] = []
            days[day_str].append(ev)

        for day_str in sorted(days.keys()):
            # Заголовок дня
            try:
                d = datetime.fromisoformat(day_str)
                day_label = d.strftime("%d %B, %A")
            except Exception:
                day_label = day_str

            is_today = day_str == date.today().isoformat()

            self.events_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        day_label + (" — Сегодня" if is_today else ""),
                        size=13,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE if is_today else ft.Colors.with_opacity(0.85, ft.Colors.ON_SURFACE),
                    ),
                    padding=ft.padding.only(top=12, bottom=4),
                )
            )

            for ev in days[day_str]:
                self.events_list.controls.append(self._event_card(ev))

    def _event_card(self, event: dict) -> ft.Container:
        """Карточка события."""
        start = str(event.get("start_time", ""))
        time_str = start[11:16] if len(start) > 11 else "Весь день"
        color = event.get("color", "") or ft.Colors.ON_SURFACE

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=4, height=36, border_radius=2, bgcolor=color),
                    ft.Column(
                        [
                            ft.Text(
                                event.get("title", ""),
                                size=14,
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.ON_SURFACE,
                            ),
                            ft.Row(
                                [
                                    ft.Text(time_str, size=12, color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE)),
                                    ft.Text(
                                        event.get("location", ""),
                                        size=12,
                                        color=ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE),
                                        visible=bool(event.get("location")),
                                    ),
                                ],
                                spacing=12,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_HORIZ,
                        icon_size=16,
                        items=[
                            ft.PopupMenuItem(content=ft.Text("Редактировать"), on_click=lambda e, ev=event: self._edit_event(ev)),
                            ft.PopupMenuItem(content=ft.Text("Удалить"), on_click=lambda e, ev=event: self._delete_event(ev["id"])),
                        ],
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.all(10),
            border_radius=8,
            border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE)),
            ink=True,
        )

    def _format_month(self, d: date) -> str:
        months = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        return f"{months[d.month - 1]} {d.year}"

    def _prev_month(self, e):
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.date_label.value = self._format_month(self.current_date)
        self._load_events()
        self.page.update()

    def _next_month(self, e):
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.date_label.value = self._format_month(self.current_date)
        self._load_events()
        self.page.update()

    def _go_today(self, e):
        self.current_date = date.today()
        self.date_label.value = self._format_month(self.current_date)
        self._load_events()
        self.page.update()

    def _on_view_change(self, e):
        selected = e.control.selected
        if selected:
            self.view_mode = list(selected)[0]

    def _show_create_dialog(self, e=None):
        """Диалог создания события."""
        self._show_event_dialog()

    def _edit_event(self, event: dict):
        self._show_event_dialog(event)

    def _show_event_dialog(self, event: dict = None):
        is_edit = event is not None
        title_field = ft.TextField(label="Название", value=event.get("title", "") if event else "", autofocus=True)
        desc_field = ft.TextField(label="Описание", value=event.get("description", "") if event else "", multiline=True, min_lines=2)
        start_field = ft.TextField(label="Начало (YYYY-MM-DD HH:MM)", value=str(event.get("start_time", ""))[:16] if event else datetime.now().strftime("%Y-%m-%d %H:%M"))
        end_field = ft.TextField(label="Конец (YYYY-MM-DD HH:MM)", value=str(event.get("end_time", "") or "")[:16] if event else "")
        location_field = ft.TextField(label="Место", value=event.get("location", "") if event else "")

        def on_save(e):
            title = title_field.value
            if not title or not title.strip():
                return
            if is_edit:
                self.db.update_event(
                    event["id"],
                    title=title.strip(),
                    description=desc_field.value or "",
                    start_time=start_field.value,
                    end_time=end_field.value or None,
                    location=location_field.value or "",
                )
            else:
                self.db.create_event(
                    title=title.strip(),
                    start_time=start_field.value,
                    end_time=end_field.value or None,
                    description=desc_field.value or "",
                    location=location_field.value or "",
                )
            self.page.pop_dialog()
            self._load_events()
            self.page.update()
            event_bus.emit(Events.EVENT_CREATED if not is_edit else Events.EVENT_UPDATED)

        dialog = ft.AlertDialog(
            title=ft.Text("Редактировать событие" if is_edit else "Новое событие"),
            content=ft.Column(
                [title_field, desc_field, start_field, end_field, location_field],
                tight=True, spacing=12, width=400,
            ),
            actions=[
                ft.TextButton(content=ft.Text("Отмена"), on_click=lambda e: self.page.pop_dialog()),
                ft.FilledButton(content=ft.Text("Сохранить"), on_click=on_save),
            ],
        )
        self.page.show_dialog(dialog)

    def _delete_event(self, event_id: int):
        self.db.delete_event(event_id)
        self._load_events()
        self.page.update()
        event_bus.emit(Events.EVENT_DELETED, {"id": event_id})
