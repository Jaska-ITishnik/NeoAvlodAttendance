"""
Finite State Machine (FSM), Routers
"""

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from bot.handlers import routers

load_dotenv(".env")
dp = Dispatcher()
TOKEN = os.getenv('BOT_TOKEN')


async def on_startup(bot: Bot):
    pass


async def on_shutdown(bot: Bot):
    pass


async def main() -> None:
    bot = Bot(token=TOKEN)  # noqa
    dp.include_routers(*routers)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
