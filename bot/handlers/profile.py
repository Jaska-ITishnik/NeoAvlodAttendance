from datetime import date, datetime
from html import escape
import re

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from bot.buttons import MainMenu, main_menu_keyboard
from bot.user_preferences import (
    ensure_user,
    get_user_by_telegram_id,
    is_placeholder_dob,
    is_placeholder_email,
    is_placeholder_phone,
    language_for_event_user,
)
from db import database
from db.models import Order, Student

router = Router(name="profile")

CANCEL_TEXTS = {
    "uz": "❌ Bekor qilish",
    "ru": "❌ Отмена",
}
GENDER_LABELS = {
    "uz": {
        "male": "Erkak",
        "femail": "Ayol",
        "other": "Boshqa",
    },
    "ru": {
        "male": "Мужчина",
        "femail": "Женщина",
        "other": "Другое",
    },
}
LANGUAGE_LABELS = {
    "uz": "O'zbekcha",
    "ru": "Русский",
}


class ProfileEdit(StatesGroup):
    waiting_full_name = State()
    waiting_phone = State()
    waiting_email = State()
    waiting_dob = State()


def _cancel_keyboard(language_code: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXTS[language_code])]],
        resize_keyboard=True,
        input_field_placeholder={
            "uz": "Bekor qilish",
            "ru": "Отмена",
        }[language_code],
    )


def _profile_keyboard(language_code: str) -> InlineKeyboardMarkup:
    if language_code == "ru":
        rows = [
            [
                InlineKeyboardButton(text="✏️ Имя", callback_data="profile:edit:name"),
                InlineKeyboardButton(text="📞 Телефон", callback_data="profile:edit:phone"),
            ],
            [
                InlineKeyboardButton(text="📧 Email", callback_data="profile:edit:email"),
                InlineKeyboardButton(text="🎂 Дата рождения", callback_data="profile:edit:dob"),
            ],
            [InlineKeyboardButton(text="⚧ Пол", callback_data="profile:edit:gender")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="profile:refresh")],
        ]
    else:
        rows = [
            [
                InlineKeyboardButton(text="✏️ Ism-familiya", callback_data="profile:edit:name"),
                InlineKeyboardButton(text="📞 Telefon", callback_data="profile:edit:phone"),
            ],
            [
                InlineKeyboardButton(text="📧 Email", callback_data="profile:edit:email"),
                InlineKeyboardButton(text="🎂 Tug'ilgan sana", callback_data="profile:edit:dob"),
            ],
            [InlineKeyboardButton(text="⚧ Jins", callback_data="profile:edit:gender")],
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data="profile:refresh")],
        ]

    return InlineKeyboardMarkup(inline_keyboard=rows)


def _gender_keyboard(language_code: str) -> InlineKeyboardMarkup:
    labels = GENDER_LABELS[language_code]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=labels["male"], callback_data="profile:gender:male")],
            [InlineKeyboardButton(text=labels["femail"], callback_data="profile:gender:femail")],
            [InlineKeyboardButton(text=labels["other"], callback_data="profile:gender:other")],
        ]
    )


def _display_value(value: str | None, language_code: str) -> str:
    if value:
        return escape(value)
    return {"uz": "Kiritilmagan", "ru": "Не указано"}[language_code]


def _display_phone(user: Student | None, telegram_id: int, language_code: str) -> str:
    if user is None or is_placeholder_phone(user.phone, telegram_id):
        return _display_value(None, language_code)
    return escape(user.phone)


def _display_email(user: Student | None, telegram_id: int, language_code: str) -> str:
    if user is None or is_placeholder_email(user.email, telegram_id):
        return _display_value(None, language_code)
    return escape(user.email)


def _display_dob(user: Student | None, language_code: str) -> str:
    if user is None or is_placeholder_dob(user.dob):
        return _display_value(None, language_code)
    return user.dob.strftime("%d.%m.%Y")


def _count_orders(user: Student | None) -> int:
    if user is None:
        return 0
    return database.execute(
        select(func.count(Order.id)).where(Order.user_id == user.id)
    ).scalar_one()


def _profile_text(user: Student | None, telegram_user, language_code: str) -> str:
    telegram_id = telegram_user.id
    username = f"@{telegram_user.username}" if telegram_user.username else None
    first_name = user.first_name if user else telegram_user.first_name
    last_name = None if user is None or user.last_name == "-" else user.last_name
    gender = user.gender if user else "other"
    user_language = user.language_code if user else language_code
    order_count = _count_orders(user)

    if language_code == "ru":
        return (
            "👤 <b>Профиль</b>\n\n"
            f"🆔 <b>Telegram ID:</b> <code>{telegram_id}</code>\n"
            f"🔗 <b>Username:</b> {_display_value(username, language_code)}\n"
            f"👤 <b>Имя:</b> {_display_value(first_name, language_code)}\n"
            f"👥 <b>Фамилия:</b> {_display_value(last_name, language_code)}\n"
            f"⚧ <b>Пол:</b> {GENDER_LABELS[language_code].get(gender, gender)}\n"
            f"📞 <b>Телефон:</b> {_display_phone(user, telegram_id, language_code)}\n"
            f"📧 <b>Email:</b> {_display_email(user, telegram_id, language_code)}\n"
            f"🎂 <b>Дата рождения:</b> {_display_dob(user, language_code)}\n"
            f"🌐 <b>Язык:</b> {LANGUAGE_LABELS.get(user_language, LANGUAGE_LABELS['uz'])}\n"
            f"📦 <b>Заказы:</b> {order_count}\n\n"
            "Нажмите кнопку ниже, чтобы изменить данные."
        )

    return (
        "👤 <b>Profil</b>\n\n"
        f"🆔 <b>Telegram ID:</b> <code>{telegram_id}</code>\n"
        f"🔗 <b>Username:</b> {_display_value(username, language_code)}\n"
        f"👤 <b>Ism:</b> {_display_value(first_name, language_code)}\n"
        f"👥 <b>Familiya:</b> {_display_value(last_name, language_code)}\n"
        f"⚧ <b>Jins:</b> {GENDER_LABELS[language_code].get(gender, gender)}\n"
        f"📞 <b>Telefon:</b> {_display_phone(user, telegram_id, language_code)}\n"
        f"📧 <b>Email:</b> {_display_email(user, telegram_id, language_code)}\n"
        f"🎂 <b>Tug'ilgan sana:</b> {_display_dob(user, language_code)}\n"
        f"🌐 <b>Til:</b> {LANGUAGE_LABELS.get(user_language, LANGUAGE_LABELS['uz'])}\n"
        f"📦 <b>Buyurtmalar:</b> {order_count}\n\n"
        "Ma'lumotlarni o'zgartirish uchun quyidagi tugmalardan foydalaning."
    )


def _split_full_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(maxsplit=1)
    first_name = parts[0][:30]
    last_name = parts[1][:30] if len(parts) > 1 else "-"
    return first_name, last_name


def _normalize_phone(value: str) -> str:
    raw_phone = value.strip()
    digits = "".join(char for char in raw_phone if char.isdigit())
    if len(digits) < 7:
        raise ValueError("phone")
    return (f"+{digits}" if raw_phone.startswith("+") else digits)[:30]


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("email")
    return email[:100]


def _parse_dob(value: str) -> date:
    value = value.strip()
    for date_format in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            parsed = datetime.strptime(value, date_format).date()
            break
        except ValueError:
            continue
    else:
        raise ValueError("date")

    if parsed > date.today():
        raise ValueError("future")
    return parsed


def _phone_conflict_exists(phone: str, telegram_id: int) -> bool:
    owner = database.execute(select(Student).where(Student.phone == phone)).scalars().first()
    return owner is not None and owner.telegram_id != telegram_id


def _email_conflict_exists(email: str, telegram_id: int) -> bool:
    owner = database.execute(select(Student).where(Student.email == email)).scalars().first()
    return owner is not None and owner.telegram_id != telegram_id


def _commit_profile_update(user: Student) -> bool:
    try:
        database.add(user)
        database.commit()
    except IntegrityError:
        database.rollback()
        return False
    except Exception:
        database.rollback()
        raise
    return True


async def _send_profile(message: Message) -> None:
    language_code = language_for_event_user(message.from_user)
    if message.from_user is None:
        await message.answer(
            {"uz": "Foydalanuvchi aniqlanmadi.", "ru": "Пользователь не определен."}[language_code],
            reply_markup=main_menu_keyboard(language_code),
        )
        return

    user = get_user_by_telegram_id(message.from_user.id)
    await message.answer(
        _profile_text(user, message.from_user, language_code),
        reply_markup=_profile_keyboard(language_code),
        parse_mode="HTML",
    )


@router.message(Command(commands=["profile"]))
@router.message(F.text.in_(MainMenu.texts("profile")))
async def profile_handler(message: Message) -> None:
    await _send_profile(message)


@router.callback_query(F.data == "profile:refresh")
async def profile_refresh_handler(callback_query: CallbackQuery) -> None:
    language_code = language_for_event_user(callback_query.from_user)
    user = get_user_by_telegram_id(callback_query.from_user.id)
    if callback_query.message is not None:
        await callback_query.message.edit_text(
            _profile_text(user, callback_query.from_user, language_code),
            reply_markup=_profile_keyboard(language_code),
            parse_mode="HTML",
        )
    await callback_query.answer({"uz": "Yangilandi.", "ru": "Обновлено."}[language_code])


@router.callback_query(F.data.startswith("profile:edit:"))
async def profile_edit_start_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    language_code = language_for_event_user(callback_query.from_user)
    if callback_query.from_user is None:
        await callback_query.answer(
            {"uz": "Foydalanuvchi aniqlanmadi.", "ru": "Пользователь не определен."}[language_code],
            show_alert=True,
        )
        return

    field = callback_query.data.rsplit(":", maxsplit=1)[-1]
    ensure_user(callback_query.from_user, language_code)
    await state.clear()

    if field == "name":
        await state.set_state(ProfileEdit.waiting_full_name)
        text = {
            "uz": "👤 Ism va familiyangizni kiriting. Masalan: Ali Valiyev",
            "ru": "👤 Введите имя и фамилию. Например: Али Валиев",
        }[language_code]
    elif field == "phone":
        await state.set_state(ProfileEdit.waiting_phone)
        text = {
            "uz": "📞 Telefon raqamingizni kiriting. Masalan: +998901234567",
            "ru": "📞 Введите номер телефона. Например: +998901234567",
        }[language_code]
    elif field == "email":
        await state.set_state(ProfileEdit.waiting_email)
        text = {
            "uz": "📧 Email manzilingizni kiriting.",
            "ru": "📧 Введите email.",
        }[language_code]
    elif field == "dob":
        await state.set_state(ProfileEdit.waiting_dob)
        text = {
            "uz": "🎂 Tug'ilgan sanani kiriting: YYYY-MM-DD yoki DD.MM.YYYY",
            "ru": "🎂 Введите дату рождения: YYYY-MM-DD или DD.MM.YYYY",
        }[language_code]
    elif field == "gender":
        if callback_query.message is None:
            await callback_query.answer()
            return
        await callback_query.message.answer(
            {"uz": "⚧ Jinsingizni tanlang:", "ru": "⚧ Выберите пол:"}[language_code],
            reply_markup=_gender_keyboard(language_code),
        )
        await callback_query.answer()
        return
    else:
        await callback_query.answer(
            {"uz": "Maydon topilmadi.", "ru": "Поле не найдено."}[language_code],
            show_alert=True,
        )
        return

    if callback_query.message is not None:
        await callback_query.message.answer(text, reply_markup=_cancel_keyboard(language_code))
    await callback_query.answer()


@router.message(StateFilter(ProfileEdit.waiting_full_name, ProfileEdit.waiting_phone, ProfileEdit.waiting_email, ProfileEdit.waiting_dob), F.text.in_(set(CANCEL_TEXTS.values())))
async def profile_edit_cancel_handler(message: Message, state: FSMContext) -> None:
    language_code = language_for_event_user(message.from_user)
    await state.clear()
    await message.answer(
        {"uz": "❌ Profil tahriri bekor qilindi.", "ru": "❌ Редактирование профиля отменено."}[language_code],
        reply_markup=main_menu_keyboard(language_code),
    )


@router.message(StateFilter(ProfileEdit.waiting_full_name, ProfileEdit.waiting_phone, ProfileEdit.waiting_email, ProfileEdit.waiting_dob), F.text.in_(MainMenu.all_texts()))
async def profile_edit_menu_handler(message: Message, state: FSMContext) -> None:
    language_code = language_for_event_user(message.from_user)
    await state.clear()
    await message.answer(
        {
            "uz": "Profil tahriri yopildi. Kerakli bo'limni menyudan qayta tanlang.",
            "ru": "Редактирование профиля закрыто. Снова выберите нужный раздел в меню.",
        }[language_code],
        reply_markup=main_menu_keyboard(language_code),
    )


@router.message(ProfileEdit.waiting_full_name)
async def profile_name_save_handler(message: Message, state: FSMContext) -> None:
    language_code = language_for_event_user(message.from_user)
    full_name = (message.text or "").strip()
    if len(full_name) < 2:
        await message.answer({"uz": "Ismni to'liqroq kiriting.", "ru": "Введите имя подробнее."}[language_code])
        return

    user = ensure_user(message.from_user, language_code)
    user.first_name, user.last_name = _split_full_name(full_name)
    _commit_profile_update(user)
    await state.clear()
    await message.answer(
        {"uz": "✅ Ism-familiya saqlandi.", "ru": "✅ Имя сохранено."}[language_code],
        reply_markup=main_menu_keyboard(language_code),
    )
    await _send_profile(message)


@router.message(ProfileEdit.waiting_phone)
async def profile_phone_save_handler(message: Message, state: FSMContext) -> None:
    language_code = language_for_event_user(message.from_user)
    raw_phone = message.contact.phone_number if message.contact else message.text
    if not raw_phone:
        await message.answer({"uz": "Telefon raqamni kiriting.", "ru": "Введите номер телефона."}[language_code])
        return

    try:
        phone = _normalize_phone(raw_phone)
    except ValueError:
        await message.answer({"uz": "Telefon raqam noto'g'ri.", "ru": "Неверный номер телефона."}[language_code])
        return

    if _phone_conflict_exists(phone, message.from_user.id):
        await message.answer(
            {
                "uz": "Bu telefon raqam boshqa profilga biriktirilgan.",
                "ru": "Этот номер телефона уже привязан к другому профилю.",
            }[language_code]
        )
        return

    user = ensure_user(message.from_user, language_code)
    user.phone = phone
    if not _commit_profile_update(user):
        await message.answer({"uz": "Telefon raqam saqlanmadi.", "ru": "Номер телефона не сохранен."}[language_code])
        return

    await state.clear()
    await message.answer(
        {"uz": "✅ Telefon raqam saqlandi.", "ru": "✅ Номер телефона сохранен."}[language_code],
        reply_markup=main_menu_keyboard(language_code),
    )
    await _send_profile(message)


@router.message(ProfileEdit.waiting_email)
async def profile_email_save_handler(message: Message, state: FSMContext) -> None:
    language_code = language_for_event_user(message.from_user)
    try:
        email = _normalize_email(message.text or "")
    except ValueError:
        await message.answer({"uz": "Email noto'g'ri kiritildi.", "ru": "Email введен неверно."}[language_code])
        return

    if _email_conflict_exists(email, message.from_user.id):
        await message.answer(
            {
                "uz": "Bu email boshqa profilga biriktirilgan.",
                "ru": "Этот email уже привязан к другому профилю.",
            }[language_code]
        )
        return

    user = ensure_user(message.from_user, language_code)
    user.email = email
    if not _commit_profile_update(user):
        await message.answer({"uz": "Email saqlanmadi.", "ru": "Email не сохранен."}[language_code])
        return

    await state.clear()
    await message.answer(
        {"uz": "✅ Email saqlandi.", "ru": "✅ Email сохранен."}[language_code],
        reply_markup=main_menu_keyboard(language_code),
    )
    await _send_profile(message)


@router.message(ProfileEdit.waiting_dob)
async def profile_dob_save_handler(message: Message, state: FSMContext) -> None:
    language_code = language_for_event_user(message.from_user)
    try:
        dob = _parse_dob(message.text or "")
    except ValueError:
        await message.answer(
            {
                "uz": "Sana noto'g'ri. Masalan: 2000-12-31 yoki 31.12.2000",
                "ru": "Неверная дата. Например: 2000-12-31 или 31.12.2000",
            }[language_code]
        )
        return

    user = ensure_user(message.from_user, language_code)
    user.dob = dob
    _commit_profile_update(user)
    await state.clear()
    await message.answer(
        {"uz": "✅ Tug'ilgan sana saqlandi.", "ru": "✅ Дата рождения сохранена."}[language_code],
        reply_markup=main_menu_keyboard(language_code),
    )
    await _send_profile(message)


@router.callback_query(F.data.startswith("profile:gender:"))
async def profile_gender_save_handler(callback_query: CallbackQuery) -> None:
    language_code = language_for_event_user(callback_query.from_user)
    gender = callback_query.data.rsplit(":", maxsplit=1)[-1]
    if gender not in GENDER_LABELS["uz"]:
        await callback_query.answer(
            {"uz": "Jins topilmadi.", "ru": "Пол не найден."}[language_code],
            show_alert=True,
        )
        return

    user = ensure_user(callback_query.from_user, language_code)
    user.gender = gender
    _commit_profile_update(user)
    if callback_query.message is not None:
        await callback_query.message.edit_text(
            _profile_text(user, callback_query.from_user, language_code),
            reply_markup=_profile_keyboard(language_code),
            parse_mode="HTML",
        )
    await callback_query.answer({"uz": "Saqlandi.", "ru": "Сохранено."}[language_code])
