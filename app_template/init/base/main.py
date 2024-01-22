"""
Точка входа для запуска бота
"""
import asyncio
import logging.config

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

import djgram
from configs import LOGGING_CONFIG, TELEGRAM_BOT_TOKEN

# noinspection PyUnresolvedReferences
from djgram.db.models import BaseModel  # noqa: F401 нужно для корректной работы alembic

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
main_router = Router()


@main_router.message(Command("start"))
async def start_handler(message: Message):
    """
    Обработчик команды /start
    """

    await message.answer("Стартовое сообщение\n\nВведите команду /help для получения помощи")


@main_router.message(Command("help"))
async def help_handler(message: Message):
    """
    Обработчик команды /help
    """

    await message.answer(
        "Тестовый эхо бот. Пока умеет только пересылать вам ваши сообщения.\n\n/help - помощь\n/start - запустить бота"
    )


@main_router.message()
async def echo_handler(message: Message):
    """
    Эхо
    """

    await message.copy_to(message.chat.id)


def setup_routers(dp: Dispatcher) -> None:
    """
    Установка роутеров
    """
    dp.include_router(main_router)

    logger.info("Routers setup")


async def main() -> None:
    """
    Точка входа в бота
    """

    storage = MemoryStorage()  # todo:  Стоит поменять на RedisStorage
    dp = Dispatcher(storage=storage)
    bot = Bot(TELEGRAM_BOT_TOKEN)

    djgram.setup(dp, analytics=False)
    setup_routers(dp)

    await dp.start_polling(bot, skip_updates=False)


if __name__ == "__main__":
    asyncio.run(main())
