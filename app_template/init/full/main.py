"""
Точка входа для запуска бота
"""

import asyncio
import logging.config

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import UpdateType
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.redis import (
    DefaultKeyBuilder,  # pyright: ignore [reportPrivateImportUsage]
    RedisStorage,
)
from aiogram.types import Message
from redis.asyncio.client import Redis

from configs import (
    LOGGING_CONFIG,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    REDIS_STORAGE_DB,
    REDIS_USER,
    TELEGRAM_BOT_TOKEN,
)

# noinspection PyUnresolvedReferences
from djgram.db.models import BaseModel  # noqa: F401 нужно для корректной работы alembic
from djgram.setup import setup_djgram

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
main_router = Router()


@main_router.message(CommandStart())
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

    redis_for_storage = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        username=REDIS_USER,
        password=REDIS_PASSWORD,
        db=REDIS_STORAGE_DB,
    )

    storage = RedisStorage(redis_for_storage, key_builder=DefaultKeyBuilder(with_destiny=True))

    dp = Dispatcher(storage=storage)
    bot = Bot(TELEGRAM_BOT_TOKEN)

    setup_djgram(dp)
    setup_routers(dp)

    await dp.start_polling(bot, skip_updates=False, allowed_updates=list(UpdateType))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting sown")
