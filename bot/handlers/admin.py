from __future__ import annotations

from datetime import date, datetime

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot.buttons import (
    BACK_BUTTON,
    EVEN_BUTTON,
    GROUPS_BUTTON,
    ODD_BUTTON,
    STATISTICS_BUTTON,
    AttendanceCallback,
    GroupCallback,
    StatisticsCallback,
    attendance_confirmation_inline,
    attendance_inline,
    group_detail_inline,
    groups_inline,
    groups_menu,
    main_menu,
    statistics_group_inline,
    statistics_inline,
)
from bot.filters import AdminFilter
from bot.services.attendance import (
    APP_TIMEZONE,
    find_current_schedule,
    get_attendance_snapshot,
    get_group_details,
    get_group_statistics,
    get_overall_statistics,
    list_groups,
    save_attendance,
)
from bot.states import AttendanceStates
from db.base import db
from db.models import GroupSchedule


router = Router(name="admin")
WEEKDAYS = ("Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba")


async def _edit(message: Message, text: str, reply_markup=None) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            raise


def _period_title(period: str) -> str:
    return "1️⃣ Toq kunlar" if period == "odd" else "2️⃣ Juft kunlar"


def _format_group(group_id: int) -> tuple[str, object] | None:
    details = get_group_details(group_id)
    if details is None:
        return None
    schedule_lines = [
        f"• {WEEKDAYS[item.weekday]}: {item.start_time:%H:%M}–{item.end_time:%H:%M}"
        for item in details.schedules
    ]
    text = (
        "📚 GURUH MA’LUMOTI\n\n"
        f"🏷 Guruh: {details.group.name}\n"
        f"📖 Kurs: {details.group.course_name}\n"
        f"👥 Faol o‘quvchilar: {details.student_count}\n\n"
        "🗓 Dars jadvali:\n"
        + ("\n".join(schedule_lines) if schedule_lines else "• Jadval belgilanmagan")
    )
    return text, details


async def _render_groups(message: Message, period: str, page: int = 0) -> None:
    groups = list_groups(period)
    body = (
        f"{_period_title(period)}\n\n"
        f"Faol guruhlar: {len(groups)} ta\n"
        "Batafsil ma’lumot uchun guruhni tanlang."
    )
    if not groups:
        body += "\n\nHozircha bu kunlarda faol guruh yo‘q."
    await _edit(message, body, groups_inline(groups, period, page))


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not await AdminFilter()(message):
        await message.answer("⛔️ Bu bot faqat administratorlar uchun mo‘ljallangan.")
        return
    await message.answer(
        "Assalomu alaykum! Davomat boshqaruv bo‘limiga xush kelibsiz.\nKerakli bo‘limni tanlang:",
        reply_markup=main_menu(),
    )


@router.message(AdminFilter(), F.text == GROUPS_BUTTON)
async def open_groups_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("📅 Guruhlarning dars kunini tanlang:", reply_markup=groups_menu())


@router.message(AdminFilter(), F.text == BACK_BUTTON)
async def back_to_main(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu())


@router.message(AdminFilter(), F.text.in_({ODD_BUTTON, EVEN_BUTTON}))
async def choose_period(message: Message) -> None:
    period = "odd" if message.text == ODD_BUTTON else "even"
    groups = list_groups(period)
    text = (
        f"{_period_title(period)}\n\n"
        f"Faol guruhlar: {len(groups)} ta\n"
        "Batafsil ma’lumot uchun guruhni tanlang."
    )
    if not groups:
        text += "\n\nHozircha bu kunlarda faol guruh yo‘q."
    await message.answer(text, reply_markup=groups_inline(groups, period, 0))


@router.callback_query(AdminFilter(), GroupCallback.filter(F.action == "list"))
async def group_list_callback(callback: CallbackQuery, callback_data: GroupCallback) -> None:
    if isinstance(callback.message, Message):
        await _render_groups(callback.message, callback_data.period, callback_data.page)
    await callback.answer()


@router.callback_query(AdminFilter(), GroupCallback.filter(F.action == "detail"))
async def group_detail(callback: CallbackQuery, callback_data: GroupCallback) -> None:
    result = _format_group(callback_data.group_id)
    if result is None:
        await callback.answer("Guruh topilmadi yoki faol emas.", show_alert=True)
        return
    text, _details = result
    if isinstance(callback.message, Message):
        await _edit(
            callback.message,
            text,
            group_detail_inline(callback_data.group_id, callback_data.period, callback_data.page),
        )
    await callback.answer()


async def _attendance_data(state: FSMContext, callback_data: AttendanceCallback):
    data = await state.get_data()
    if (
        data.get("group_id") != callback_data.group_id
        or data.get("schedule_id") != callback_data.schedule_id
    ):
        return None
    schedule = db.scalar(
        select(GroupSchedule).where(GroupSchedule.id == callback_data.schedule_id)
    )
    if schedule is None:
        return None
    lesson_date = date.fromisoformat(data["lesson_date"])
    snapshot = get_attendance_snapshot(callback_data.group_id, schedule, lesson_date)
    if snapshot is None:
        return None
    selected = set(data.get("selected_ids", []))
    selected.intersection_update(student.id for student in snapshot.students)
    if selected != set(data.get("selected_ids", [])):
        await state.update_data(selected_ids=list(selected))
    return data, snapshot, selected


async def _render_attendance(
    message: Message,
    state: FSMContext,
    callback_data: AttendanceCallback,
    page: int,
) -> bool:
    loaded = await _attendance_data(state, callback_data)
    if loaded is None:
        return False
    _data, snapshot, selected = loaded
    total = len(snapshot.students)
    text = (
        "📝 DAVOMAT BELGILASH\n\n"
        f"📚 {snapshot.group.name} · {snapshot.group.course_name}\n"
        f"🕐 {snapshot.schedule.start_time:%H:%M}–{snapshot.schedule.end_time:%H:%M}\n"
        f"📅 {date.fromisoformat(_data['lesson_date']):%d.%m.%Y}\n\n"
        f"✅ Bor: {len(selected)}\n"
        f"❌ Yo‘q: {total - len(selected)}\n"
        f"👥 Jami: {total}\n\n"
        "O‘quvchi ustiga bosib holatini almashtiring."
    )
    await _edit(
        message,
        text,
        attendance_inline(
            snapshot.students,
            selected,
            snapshot.group.id,
            snapshot.schedule.id,
            page,
        ),
    )
    return True


@router.callback_query(AdminFilter(), AttendanceCallback.filter(F.action == "start"))
async def attendance_start(
    callback: CallbackQuery,
    callback_data: AttendanceCallback,
    state: FSMContext,
) -> None:
    schedule, error = find_current_schedule(callback_data.group_id)
    if schedule is None:
        await callback.answer(error or "Davomatni hozir boshlash mumkin emas.", show_alert=True)
        return
    today = datetime.now(APP_TIMEZONE).date()
    snapshot = get_attendance_snapshot(callback_data.group_id, schedule, today)
    if snapshot is None or not snapshot.students:
        await callback.answer("Bu guruhda faol o‘quvchilar yo‘q.", show_alert=True)
        return
    await state.set_state(AttendanceStates.marking)
    await state.set_data(
        {
            "group_id": callback_data.group_id,
            "schedule_id": schedule.id,
            "lesson_date": today.isoformat(),
            "selected_ids": list(snapshot.present_student_ids),
        }
    )
    active_callback = AttendanceCallback(
        action="page", group_id=callback_data.group_id, schedule_id=schedule.id, page=0
    )
    if isinstance(callback.message, Message):
        await _render_attendance(callback.message, state, active_callback, 0)
    await callback.answer("Davomat ochildi")


@router.callback_query(
    AdminFilter(), AttendanceStates.marking, AttendanceCallback.filter(F.action == "toggle")
)
async def attendance_toggle(
    callback: CallbackQuery,
    callback_data: AttendanceCallback,
    state: FSMContext,
) -> None:
    loaded = await _attendance_data(state, callback_data)
    if loaded is None:
        await callback.answer("Davomat sessiyasi eskirgan.", show_alert=True)
        return
    _data, snapshot, selected = loaded
    allowed_ids = {student.id for student in snapshot.students}
    if callback_data.student_id not in allowed_ids:
        await callback.answer("O‘quvchi topilmadi.", show_alert=True)
        return
    if callback_data.student_id in selected:
        selected.remove(callback_data.student_id)
    else:
        selected.add(callback_data.student_id)
    await state.update_data(selected_ids=list(selected))
    if isinstance(callback.message, Message):
        await _render_attendance(callback.message, state, callback_data, callback_data.page)
    await callback.answer("Holat yangilandi")


@router.callback_query(
    AdminFilter(), AttendanceCallback.filter(F.action.in_({"page", "all", "none", "edit"}))
)
async def attendance_controls(
    callback: CallbackQuery,
    callback_data: AttendanceCallback,
    state: FSMContext,
) -> None:
    loaded = await _attendance_data(state, callback_data)
    if loaded is None:
        await callback.answer("Davomat sessiyasi eskirgan.", show_alert=True)
        return
    _data, snapshot, _selected = loaded
    if callback_data.action == "all":
        await state.update_data(selected_ids=[student.id for student in snapshot.students])
    elif callback_data.action == "none":
        await state.update_data(selected_ids=[])
    elif callback_data.action == "edit":
        await state.set_state(AttendanceStates.marking)
    if isinstance(callback.message, Message):
        await _render_attendance(callback.message, state, callback_data, callback_data.page)
    await callback.answer()


@router.callback_query(
    AdminFilter(), AttendanceStates.marking, AttendanceCallback.filter(F.action == "confirm")
)
async def attendance_confirm(
    callback: CallbackQuery,
    callback_data: AttendanceCallback,
    state: FSMContext,
) -> None:
    loaded = await _attendance_data(state, callback_data)
    if loaded is None:
        await callback.answer("Davomat sessiyasi eskirgan.", show_alert=True)
        return
    _data, snapshot, selected = loaded
    await state.set_state(AttendanceStates.confirming)
    text = (
        "⚠️ DAVOMATNI TASDIQLASH\n\n"
        f"📚 {snapshot.group.name}\n"
        f"👥 Jami: {len(snapshot.students)}\n"
        f"✅ Bor: {len(selected)}\n"
        f"❌ Yo‘q: {len(snapshot.students) - len(selected)}\n\n"
        "Ma’lumotlarni saqlaymizmi?"
    )
    if isinstance(callback.message, Message):
        await _edit(
            callback.message,
            text,
            attendance_confirmation_inline(
                snapshot.group.id, snapshot.schedule.id, callback_data.page
            ),
        )
    await callback.answer()


@router.callback_query(
    AdminFilter(), AttendanceStates.confirming, AttendanceCallback.filter(F.action == "save")
)
async def attendance_save(
    callback: CallbackQuery,
    callback_data: AttendanceCallback,
    state: FSMContext,
) -> None:
    loaded = await _attendance_data(state, callback_data)
    if loaded is None:
        await callback.answer("Davomat sessiyasi eskirgan.", show_alert=True)
        return
    data, snapshot, selected = loaded
    try:
        save_attendance(
            snapshot.schedule.id,
            date.fromisoformat(data["lesson_date"]),
            snapshot.students,
            selected,
            callback.from_user.id,
        )
    except Exception:
        await callback.answer("Saqlashda xatolik yuz berdi. Qayta urinib ko‘ring.", show_alert=True)
        return
    await state.clear()
    text = (
        "✅ DAVOMAT SAQLANDI\n\n"
        f"📚 {snapshot.group.name}\n"
        f"✅ Bor: {len(selected)}\n"
        f"❌ Yo‘q: {len(snapshot.students) - len(selected)}\n"
        f"👥 Jami: {len(snapshot.students)}"
    )
    period = "odd" if snapshot.schedule.weekday in (0, 2, 4) else "even"
    if isinstance(callback.message, Message):
        await _edit(
            callback.message,
            text,
            group_detail_inline(snapshot.group.id, period, 0),
        )
    await callback.answer("Muvaffaqiyatli saqlandi")


@router.callback_query(AdminFilter(), AttendanceCallback.filter(F.action == "cancel"))
async def attendance_cancel(
    callback: CallbackQuery,
    callback_data: AttendanceCallback,
    state: FSMContext,
) -> None:
    await state.clear()
    result = _format_group(callback_data.group_id)
    if result and isinstance(callback.message, Message):
        text, details = result
        period = "odd"
        if details.schedules and details.schedules[0].weekday in (1, 3, 5):
            period = "even"
        await _edit(callback.message, text, group_detail_inline(callback_data.group_id, period, 0))
    await callback.answer("Bekor qilindi")


def _overview_text(summaries) -> str:
    lessons = sum(item.lessons for item in summaries)
    present = sum(item.present for item in summaries)
    absent = sum(item.absent for item in summaries)
    total = present + absent
    percent = round(present * 100 / total, 1) if total else 0.0
    active = sum(1 for item in summaries if item.total)
    return (
        "📊 30 KUNLIK DAVOMAT\n\n"
        f"📚 Faol guruhlar: {len(summaries)}\n"
        f"📝 Davomat qilingan guruhlar: {active}\n"
        f"🗓 O‘tilgan darslar: {lessons}\n"
        f"✅ Bor belgilari: {present}\n"
        f"❌ Yo‘q belgilari: {absent}\n"
        f"📈 Umumiy qatnashuv: {percent:.1f}%\n\n"
        "Guruh kesimini ko‘rish uchun tanlang."
    )


@router.message(AdminFilter(), F.text == STATISTICS_BUTTON)
async def statistics_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    summaries = get_overall_statistics()
    await message.answer(_overview_text(summaries), reply_markup=statistics_inline(summaries, 0))


@router.callback_query(AdminFilter(), StatisticsCallback.filter(F.action == "overview"))
async def statistics_overview(
    callback: CallbackQuery, callback_data: StatisticsCallback
) -> None:
    summaries = get_overall_statistics()
    if isinstance(callback.message, Message):
        await _edit(
            callback.message,
            _overview_text(summaries),
            statistics_inline(summaries, callback_data.page),
        )
    await callback.answer()


@router.callback_query(AdminFilter(), StatisticsCallback.filter(F.action == "group"))
async def statistics_group(
    callback: CallbackQuery, callback_data: StatisticsCallback
) -> None:
    result = get_group_statistics(callback_data.group_id)
    if result is None:
        await callback.answer("Guruh topilmadi.", show_alert=True)
        return
    summary, students = result
    recorded = [item for item in students if item.total]
    attention = recorded[:5]
    leaders = sorted(recorded, key=lambda item: (-item.percent, -item.total, item.full_name))[:5]
    attention_text = "\n".join(
        f"• {item.full_name}: {item.percent:.1f}% ({item.present}/{item.total})"
        for item in attention
    ) or "• Hali ma’lumot yo‘q"
    leaders_text = "\n".join(
        f"• {item.full_name}: {item.percent:.1f}% ({item.present}/{item.total})"
        for item in leaders
    ) or "• Hali ma’lumot yo‘q"
    text = (
        "📊 GURUH STATISTIKASI · 30 KUN\n\n"
        f"📚 {summary.group_name}\n"
        f"📖 {summary.course_name}\n"
        f"🗓 Darslar: {summary.lessons}\n"
        f"✅ Bor: {summary.present}\n"
        f"❌ Yo‘q: {summary.absent}\n"
        f"📈 Qatnashuv: {summary.percent:.1f}%\n\n"
        f"🏆 Yuqori natijalar:\n{leaders_text}\n\n"
        f"⚠️ E’tibor talab qiladi:\n{attention_text}"
    )
    if isinstance(callback.message, Message):
        await _edit(callback.message, text, statistics_group_inline(callback_data.page))
    await callback.answer()


@router.callback_query(AdminFilter(), F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(AdminFilter(), F.data == "close")
async def close_inline(callback: CallbackQuery) -> None:
    if isinstance(callback.message, Message):
        await callback.message.delete()
    await callback.answer()
