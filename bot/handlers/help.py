from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.buttons import main_menu_keyboard
from bot.user_preferences import language_for_event_user

router = Router(name="help")


@router.message(Command(commands=["help"]))
async def help_command_handler(message: Message) -> None:
    language_code = language_for_event_user(message.from_user)
    text = {
        "uz": (
            "ℹ️ <b>Yordam</b>\n\n"
            "🏠 /start - Asosiy menyuni ochish\n"
            "🛍 /catalog - Mahsulotlar katalogi\n"
            "🔎 /search - Mahsulot qidirish\n"
            "🛒 /cart - Savatni ko'rish\n"
            "📦 /orders - Buyurtmalarim\n"
            "ℹ️ /help - Bot haqida yordam"
        ),
        "ru": (
            "ℹ️ <b>Помощь</b>\n\n"
            "🏠 /start - Открыть главное меню\n"
            "🛍 /catalog - Каталог товаров\n"
            "🔎 /search - Поиск товара\n"
            "🛒 /cart - Посмотреть корзину\n"
            "📦 /orders - Мои заказы\n"
            "ℹ️ /help - Помощь по боту"
        ),
    }[language_code]
    await message.answer(
        text,
        reply_markup=main_menu_keyboard(language_code),
        parse_mode="HTML",
    )
