import logging

from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram_dialog import setup_dialogs

from djgram.contrib.admin import router as admin_router
from djgram.contrib.analytics.middlewares import SaveUpdateToClickHouseMiddleware
from djgram.contrib.auth.middlewares import AuthMiddleware
from djgram.contrib.communication import router as communication_router
from djgram.contrib.logs.middlewares import TraceMiddleware
from djgram.contrib.misc.handlers import cancel_handler
from djgram.contrib.telegram.middlewares import TelegramMiddleware
from djgram.db.middlewares import DbSessionMiddleware

logger = logging.getLogger(__name__)


def setup_router(dp: Dispatcher) -> None:
    dp.message.register(cancel_handler, Command("cancel"))
    dp.include_router(communication_router)
    dp.include_router(admin_router)

    logger.info("djgram routers setup")


def setup_middlewares(dp: Dispatcher, analytics: bool) -> None:
    dp.update.outer_middleware(TraceMiddleware())
    if analytics:
        dp.update.outer_middleware(SaveUpdateToClickHouseMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(TelegramMiddleware())
    dp.update.outer_middleware(AuthMiddleware())

    logger.info("djgram middlewares setup")


def setup(dp: Dispatcher, *, analytics: bool = True) -> None:
    """
    Установка djgram

    Args:
        dp: диспетчер
        analytics: включить сохранение аналитики в ClickHouse
    """
    setup_middlewares(dp, analytics=analytics)
    setup_router(dp)
    setup_dialogs(dp)

    logger.info("djgram setup")
