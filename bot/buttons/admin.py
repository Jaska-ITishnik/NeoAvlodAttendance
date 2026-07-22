from __future__ import annotations

from math import ceil

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.services.attendance import GroupSummary
from db.models import CourseGroup, Student


GROUPS_BUTTON = "👥 Guruhlar"
STATISTICS_BUTTON = "📊 Statistika"
ODD_BUTTON = "1️⃣ Toq kunlar"
EVEN_BUTTON = "2️⃣ Juft kunlar"
BACK_BUTTON = "⬅️ Ortga qaytish"

PAGE_SIZE = 8


class GroupCallback(CallbackData, prefix="grp"):
    action: str
    group_id: int = 0
    period: str = "odd"
    page: int = 0


class AttendanceCallback(CallbackData, prefix="att"):
    action: str
    group_id: int = 0
    schedule_id: int = 0
    student_id: int = 0
    page: int = 0


class StatisticsCallback(CallbackData, prefix="stat"):
    action: str
    group_id: int = 0
    page: int = 0


def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=GROUPS_BUTTON), KeyboardButton(text=STATISTICS_BUTTON))
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Bo‘limni tanlang")


def groups_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=ODD_BUTTON), KeyboardButton(text=EVEN_BUTTON))
    builder.row(KeyboardButton(text=BACK_BUTTON))
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Dars kunlarini tanlang")


def _pagination_row(
    builder: InlineKeyboardBuilder,
    page: int,
    total_pages: int,
    previous_data: str,
    next_data: str,
) -> None:
    row = []
    if page > 0:
        row.append(InlineKeyboardButton(text="⬅️", callback_data=previous_data))
    row.append(InlineKeyboardButton(text=f"{page + 1}/{max(total_pages, 1)}", callback_data="noop"))
    if page + 1 < total_pages:
        row.append(InlineKeyboardButton(text="➡️", callback_data=next_data))
    builder.row(*row)


def groups_inline(groups: list[CourseGroup], period: str, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    total_pages = max(ceil(len(groups) / PAGE_SIZE), 1)
    page = min(max(page, 0), total_pages - 1)
    for group in groups[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]:
        builder.row(
            InlineKeyboardButton(
                text=f"📚 {group.name} · {group.course_name}",
                callback_data=GroupCallback(
                    action="detail", group_id=group.id, period=period, page=page
                ).pack(),
            )
        )
    if total_pages > 1:
        _pagination_row(
            builder,
            page,
            total_pages,
            GroupCallback(action="list", period=period, page=page - 1).pack(),
            GroupCallback(action="list", period=period, page=page + 1).pack(),
        )
    builder.row(InlineKeyboardButton(text="✖️ Yopish", callback_data="close"))
    return builder.as_markup()


def group_detail_inline(group_id: int, period: str, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Davomatni boshlash",
            callback_data=AttendanceCallback(action="start", group_id=group_id).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Guruhlarga qaytish",
            callback_data=GroupCallback(action="list", period=period, page=page).pack(),
        )
    )
    return builder.as_markup()


def attendance_inline(
    students: list[Student],
    selected_ids: set[int],
    group_id: int,
    schedule_id: int,
    page: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    total_pages = max(ceil(len(students) / PAGE_SIZE), 1)
    page = min(max(page, 0), total_pages - 1)
    for student in students[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]:
        selected = student.id in selected_ids
        builder.row(
            InlineKeyboardButton(
                text=f"{'✅' if selected else '❌'} {student.full_name[:42]}",
                callback_data=AttendanceCallback(
                    action="toggle",
                    group_id=group_id,
                    schedule_id=schedule_id,
                    student_id=student.id,
                    page=page,
                ).pack(),
            )
        )
    if total_pages > 1:
        _pagination_row(
            builder,
            page,
            total_pages,
            AttendanceCallback(
                action="page", group_id=group_id, schedule_id=schedule_id, page=page - 1
            ).pack(),
            AttendanceCallback(
                action="page", group_id=group_id, schedule_id=schedule_id, page=page + 1
            ).pack(),
        )
    builder.row(
        InlineKeyboardButton(
            text="✅ Barchasi bor",
            callback_data=AttendanceCallback(
                action="all", group_id=group_id, schedule_id=schedule_id, page=page
            ).pack(),
        ),
        InlineKeyboardButton(
            text="🧹 Tozalash",
            callback_data=AttendanceCallback(
                action="none", group_id=group_id, schedule_id=schedule_id, page=page
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="💾 Saqlash",
            callback_data=AttendanceCallback(
                action="confirm", group_id=group_id, schedule_id=schedule_id, page=page
            ).pack(),
        ),
        InlineKeyboardButton(
            text="✖️ Bekor qilish",
            callback_data=AttendanceCallback(
                action="cancel", group_id=group_id, schedule_id=schedule_id
            ).pack(),
        ),
    )
    return builder.as_markup()


def attendance_confirmation_inline(group_id: int, schedule_id: int, page: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Ha, saqlash",
            callback_data=AttendanceCallback(
                action="save", group_id=group_id, schedule_id=schedule_id, page=page
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Tahrirlash",
            callback_data=AttendanceCallback(
                action="edit", group_id=group_id, schedule_id=schedule_id, page=page
            ).pack(),
        )
    )
    return builder.as_markup()


def statistics_inline(summaries: list[GroupSummary], page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    total_pages = max(ceil(len(summaries) / PAGE_SIZE), 1)
    page = min(max(page, 0), total_pages - 1)
    for item in summaries[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]:
        icon = "🟢" if item.percent >= 80 else "🟡" if item.percent >= 60 else "🔴"
        builder.row(
            InlineKeyboardButton(
                text=f"{icon} {item.group_name} · {item.percent:.1f}%",
                callback_data=StatisticsCallback(
                    action="group", group_id=item.group_id, page=page
                ).pack(),
            )
        )
    if total_pages > 1:
        _pagination_row(
            builder,
            page,
            total_pages,
            StatisticsCallback(action="overview", page=page - 1).pack(),
            StatisticsCallback(action="overview", page=page + 1).pack(),
        )
    builder.row(InlineKeyboardButton(text="✖️ Yopish", callback_data="close"))
    return builder.as_markup()


def statistics_group_inline(page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Umumiy statistika",
                    callback_data=StatisticsCallback(action="overview", page=page).pack(),
                )
            ]
        ]
    )
