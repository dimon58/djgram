import logging

from aiogram import Dispatcher
from aiogram.filters import Command

from djgram.contrib.admin import router as admin_router
from djgram.contrib.analytics.middlewares import SaveUpdateToClickHouseMiddleware
from djgram.contrib.auth.middlewares import AuthMiddleware
from djgram.contrib.communication import router as communication_router
from djgram.contrib.misc.handlers import cancel_handler
from djgram.contrib.telegram.middlewares import TelegramMiddleware
from djgram.db.middlewares import DbSessionMiddleware

logger = logging.getLogger(__name__)


def setup_router(dp: Dispatcher):
    dp.message.register(cancel_handler, Command("cancel"))
    dp.include_router(communication_router)
    dp.include_router(admin_router)

    logger.info("djgram routers setup")


def setup_middlewares(dp: Dispatcher):
    dp.update.outer_middleware(SaveUpdateToClickHouseMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(TelegramMiddleware())
    dp.update.outer_middleware(AuthMiddleware())

    logger.info("djgram middlewares setup")


def setup(dp: Dispatcher):
    setup_middlewares(dp)
    setup_router(dp)

    logger.info("djgram setup")
