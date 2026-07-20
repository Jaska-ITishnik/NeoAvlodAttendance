from html import escape
import logging

from aiogram import F, Bot, Router
from aiogram.exceptions import TelegramAPIError
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

from bot.buttons import MainMenu, main_menu_keyboard
from bot.user_preferences import (
    get_user_by_telegram_id,
    is_placeholder_email,
    is_placeholder_phone,
    language_for_event_user,
)
from config import settings
from db.models import Student

router = Router(name="contact")
logger = logging.getLogger(__name__)

CANCEL_TEXTS = {
    "uz": "❌ Bekor qilish",
    "ru": "❌ Отмена",
}


class ContactSupport(StatesGroup):
    waiting_message = State()


def _cancel_keyboard(language_code: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXTS[language_code])]],
        resize_keyboard=True,
        input_field_placeholder={
            "uz": "Xabarni bekor qilish",
            "ru": "Отменить сообщение",
        }[language_code],
    )


def _contact_keyboard(language_code: str) -> InlineKeyboardMarkup | None:
    if not settings.admin_ids:
        return None

    text = {
        "uz": "✍️ Mas'ullarga xabar yozish",
        "ru": "✍️ Написать ответственным",
    }[language_code]
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data="contact:write")]]
    )


def _contact_text(language_code: str) -> str:
    if language_code == "ru":
        if settings.admin_ids:
            return (
                "📞 <b>Связь</b>\n\n"
                "Здесь можно отправить сообщение ответственным за интернет-магазин. "
                "Нажмите кнопку ниже и напишите вопрос, предложение или проблему."
            )
        return (
            "📞 <b>Связь</b>\n\n"
            "Ответственные за интернет-магазин пока не настроены. "
            "Добавьте Telegram ID администраторов в переменную <code>ADMIN_IDS</code>."
        )

    if settings.admin_ids:
        return (
            "📞 <b>Aloqa</b>\n\n"
            "Bu bo'lim orqali Online shop mas'ullariga xabar yuborishingiz mumkin. "
            "Quyidagi tugmani bosing va savol, taklif yoki muammoingizni yozing."
        )
    return (
        "📞 <b>Aloqa</b>\n\n"
        "Online shop mas'ullari hali sozlanmagan. "
        "Admin Telegram IDlarini <code>ADMIN_IDS</code> muhit o'zgaruvchisiga kiriting."
    )


def _optional_profile_value(value: str | None, missing: str) -> str:
    return escape(value) if value else missing


def _admin_contact_text(message: Message, user: Student | None) -> str:
    telegram_user = message.from_user
    telegram_id = telegram_user.id
    username = f"@{telegram_user.username}" if telegram_user.username else None
    full_name = " ".join(
        part for part in (
            user.first_name if user else telegram_user.first_name,
            None if user is None or user.last_name == "-" else user.last_name,
        )
        if part
    )
    phone = None if user is None or is_placeholder_phone(user.phone, telegram_id) else user.phone
    email = None if user is None or is_placeholder_email(user.email, telegram_id) else user.email

    return (
        "📩 <b>Yangi aloqa xabari</b>\n\n"
        f"👤 <b>Mijoz:</b> {_optional_profile_value(full_name, '-')}\n"
        f"🆔 <b>Telegram ID:</b> <code>{telegram_id}</code>\n"
        f"🔗 <b>Username:</b> {_optional_profile_value(username, '-')}\n"
        f"📞 <b>Telefon:</b> {_optional_profile_value(phone, '-')}\n"
        f"📧 <b>Email:</b> {_optional_profile_value(email, '-')}\n\n"
        f"💬 <b>Xabar:</b>\n{escape(message.text or '')}"
    )


async def _notify_admins(bot: Bot, message: Message) -> int:
    user = get_user_by_telegram_id(message.from_user.id)
    text = _admin_contact_text(message, user)
    sent_count = 0

    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
            sent_count += 1
        except TelegramAPIError as error:
            logger.warning("Could not send contact message to admin %s: %s", admin_id, error)

    return sent_count


@router.message(Command(commands=["contact"]))
@router.message(F.text.in_(MainMenu.texts("contact")))
async def contact_handler(message: Message) -> None:
    language_code = language_for_event_user(message.from_user)
    await message.answer(
        _contact_text(language_code),
        reply_markup=_contact_keyboard(language_code) or main_menu_keyboard(language_code),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "contact:write")
async def contact_write_start_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    language_code = language_for_event_user(callback_query.from_user)
    if not settings.admin_ids:
        await callback_query.answer(
            {
                "uz": "Adminlar sozlanmagan.",
                "ru": "Администраторы не настроены.",
            }[language_code],
            show_alert=True,
        )
        return

    await state.clear()
    await state.set_state(ContactSupport.waiting_message)
    if callback_query.message is not None:
        await callback_query.message.answer(
            {
                "uz": "💬 Mas'ullarga yuboriladigan xabarni yozing.",
                "ru": "💬 Напишите сообщение для ответственных.",
            }[language_code],
            reply_markup=_cancel_keyboard(language_code),
        )
    await callback_query.answer()


@router.message(StateFilter(ContactSupport.waiting_message), F.text.in_(set(CANCEL_TEXTS.values())))
async def contact_cancel_handler(message: Message, state: FSMContext) -> None:
    language_code = language_for_event_user(message.from_user)
    await state.clear()
    await message.answer(
        {"uz": "❌ Aloqa xabari bekor qilindi.", "ru": "❌ Сообщение отменено."}[language_code],
        reply_markup=main_menu_keyboard(language_code),
    )


@router.message(StateFilter(ContactSupport.waiting_message), F.text.in_(MainMenu.all_texts()))
async def contact_menu_handler(message: Message, state: FSMContext) -> None:
    language_code = language_for_event_user(message.from_user)
    await state.clear()
    await message.answer(
        {
            "uz": "Aloqa xabari yopildi. Kerakli bo'limni menyudan qayta tanlang.",
            "ru": "Сообщение закрыто. Снова выберите нужный раздел в меню.",
        }[language_code],
        reply_markup=main_menu_keyboard(language_code),
    )


@router.message(ContactSupport.waiting_message)
async def contact_message_handler(message: Message, state: FSMContext) -> None:
    language_code = language_for_event_user(message.from_user)
    text = (message.text or "").strip()
    if len(text) < 5:
        await message.answer(
            {"uz": "Xabarni to'liqroq yozing.", "ru": "Напишите сообщение подробнее."}[language_code]
        )
        return

    sent_count = await _notify_admins(message.bot, message)
    await state.clear()

    if sent_count == 0:
        await message.answer(
            {
                "uz": "Xabar yuborilmadi. Keyinroq qayta urinib ko'ring.",
                "ru": "Сообщение не отправлено. Попробуйте позже.",
            }[language_code],
            reply_markup=main_menu_keyboard(language_code),
        )
        return

    await message.answer(
        {
            "uz": "✅ Xabaringiz mas'ullarga yuborildi. Tez orada siz bilan bog'lanishadi.",
            "ru": "✅ Сообщение отправлено ответственным. С вами скоро свяжутся.",
        }[language_code],
        reply_markup=main_menu_keyboard(language_code),
    )
