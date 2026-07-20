from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.buttons import main_menu_keyboard
from bot.user_preferences import language_for_event_user

router = Router(name="start")


async def show_main_menu(message: Message) -> None:
    language_code = language_for_event_user(message.from_user)
    text = {
        "uz": (
            "👋 Assalomu alaykum! Online do'kon botiga xush kelibsiz.\n\n"
            "👇 Quyidagi menyulardan birini tanlang:"
        ),
        "ru": (
            "👋 Здравствуйте! Добро пожаловать в бот интернет-магазина.\n\n"
            "👇 Выберите один из разделов ниже:"
        ),
    }[language_code]
    await message.answer(
        text,
        reply_markup=main_menu_keyboard(language_code),
    )


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await show_main_menu(message)
