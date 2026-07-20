from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.buttons import MainMenu, main_menu_keyboard, normalize_language
from bot.user_preferences import ensure_user, language_for_event_user
from db import database

router = Router(name="settings")

LANGUAGE_LABELS = {
    "uz": "O'zbekcha",
    "ru": "Русский",
}


def _language_keyboard(current_language: str) -> InlineKeyboardMarkup:
    rows = []
    for language_code, label in LANGUAGE_LABELS.items():
        prefix = "✅" if language_code == current_language else "🌐"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{prefix} {label}",
                    callback_data=f"settings:lang:{language_code}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _settings_text(language_code: str) -> str:
    if language_code == "ru":
        return (
            "⚙️ <b>Настройки</b>\n\n"
            f"🌐 <b>Текущий язык:</b> {LANGUAGE_LABELS[language_code]}\n\n"
            "Выберите язык бота:"
        )

    return (
        "⚙️ <b>Sozlamalar</b>\n\n"
        f"🌐 <b>Hozirgi til:</b> {LANGUAGE_LABELS[language_code]}\n\n"
        "Bot tilini tanlang:"
    )


@router.message(Command(commands=["settings"]))
@router.message(F.text.in_(MainMenu.texts("settings")))
async def settings_handler(message: Message) -> None:
    language_code = language_for_event_user(message.from_user)
    await message.answer(
        _settings_text(language_code),
        reply_markup=_language_keyboard(language_code),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("settings:lang:"))
async def language_change_handler(callback_query: CallbackQuery) -> None:
    new_language = normalize_language(callback_query.data.rsplit(":", maxsplit=1)[-1])
    user = ensure_user(callback_query.from_user, new_language)
    user.language_code = new_language

    try:
        database.add(user)
        database.commit()
    except Exception:
        database.rollback()
        raise

    if callback_query.message is not None:
        await callback_query.message.edit_text(
            _settings_text(new_language),
            reply_markup=_language_keyboard(new_language),
            parse_mode="HTML",
        )
        await callback_query.message.answer(
            {
                "uz": "✅ Til o'zgartirildi. Asosiy menyu yangilandi.",
                "ru": "✅ Язык изменен. Главное меню обновлено.",
            }[new_language],
            reply_markup=main_menu_keyboard(new_language),
        )

    await callback_query.answer({"uz": "Til saqlandi.", "ru": "Язык сохранен."}[new_language])
