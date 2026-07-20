from aiogram import Bot
from aiogram.types import BotCommand


UZ_COMMANDS = [
    BotCommand(command="/start", description="🏠 Botni ishga tushirish"),
    BotCommand(command="/catalog", description="🛍 Mahsulotlar katalogi"),
    BotCommand(command="/search", description="🔎 Mahsulot qidirish"),
    BotCommand(command="/cart", description="🛒 Savatni ko'rish"),
    BotCommand(command="/orders", description="📦 Buyurtmalarim"),
    BotCommand(command="/profile", description="👤 Profilni ko'rish va tahrirlash"),
    BotCommand(command="/contact", description="📞 Online shop mas'ullari bilan aloqa"),
    BotCommand(command="/settings", description="⚙️ Bot sozlamalari"),
    BotCommand(command="/help", description="ℹ️ Yordam"),
]

RU_COMMANDS = [
    BotCommand(command="/start", description="🏠 Запустить бота"),
    BotCommand(command="/catalog", description="🛍 Каталог товаров"),
    BotCommand(command="/search", description="🔎 Поиск товара"),
    BotCommand(command="/cart", description="🛒 Посмотреть корзину"),
    BotCommand(command="/orders", description="📦 Мои заказы"),
    BotCommand(command="/profile", description="👤 Просмотр и редактирование профиля"),
    BotCommand(command="/contact", description="📞 Связь с ответственными магазина"),
    BotCommand(command="/settings", description="⚙️ Настройки бота"),
    BotCommand(command="/help", description="ℹ️ Помощь"),
]


async def set_default_commands(bot: Bot) -> None:
    await bot.set_my_commands(UZ_COMMANDS, language_code="uz")
    await bot.set_my_commands(RU_COMMANDS, language_code="ru")
    await bot.set_my_commands(UZ_COMMANDS)


async def delete_default_commands(bot: Bot) -> None:
    await bot.delete_my_commands(language_code="uz")
    await bot.delete_my_commands(language_code="ru")
    await bot.delete_my_commands()
