"""
Точка входа для запуска бота
"""

import asyncio
import logging.config

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart, ExceptionTypeFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState

# noinspection PyUnresolvedReferences
from djgram.db.models import BaseModel  # noqa: F401 нужно для корректной работы alembic
from djgram.setup_djgram import setup_djgram

from configs import LOGGING_CONFIG, TELEGRAM_BOT_TOKEN

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
main_router = Router()


@main_router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """
    Обработчик команды /start
    """

    await message.answer("Стартовое сообщение\n\nВведите команду /help для получения помощи")


@main_router.message(Command("help"))
async def help_handler(message: Message) -> None:
    """
    Обработчик команды /help
    """

    await message.answer(
        "Тестовый эхо бот. Пока умеет только пересылать вам ваши сообщения.\n\n/help - помощь\n/start - запустить бота",
    )


@main_router.message()
async def echo_handler(message: Message) -> None:
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


async def on_unknown_intent(event: ErrorEvent, dialog_manager: DialogManager) -> None:
    logging.error("Error in dialog: %s", event.exception)


async def on_unknown_state(event: ErrorEvent, dialog_manager: DialogManager) -> None:
    # Example of handling UnknownState Error and starting new dialog.
    logging.error("Error in dialog: %s", event.exception)


async def main() -> None:
    """
    Точка входа в бота
    """

    storage = MemoryStorage()  # TODO:  Стоит поменять на RedisStorage
    dp = Dispatcher(storage=storage)
    dp.errors.register(on_unknown_intent, ExceptionTypeFilter(UnknownIntent))
    dp.errors.register(on_unknown_state, ExceptionTypeFilter(UnknownState))
    bot = Bot(TELEGRAM_BOT_TOKEN)

    setup_djgram(dp, analytics=False)
    setup_routers(dp)

    await dp.start_polling(bot, skip_updates=False)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down")
