import logging

from aiogram import Dispatcher
from aiogram.dispatcher.middlewares.user_context import UserContextMiddleware
from aiogram.filters import Command
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.internal import DialogManagerFactory

from djgram.contrib.admin import router as admin_router
from djgram.contrib.analytics.middlewares import SaveUpdateToClickHouseMiddleware
from djgram.contrib.auth.middlewares import AuthMiddleware
from djgram.contrib.communication import router as communication_router
from djgram.contrib.limits.limiter import patch_bot_with_limiter
from djgram.contrib.logs.middlewares import TraceMiddleware
from djgram.contrib.misc.handlers import cancel_handler
from djgram.contrib.misc.middlewares import ErrorHandlingMiddleware
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
    dp.update.outer_middleware(ErrorHandlingMiddleware())
    dp.update.outer_middleware(UserContextMiddleware())
    if analytics:
        dp.update.outer_middleware(SaveUpdateToClickHouseMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(TelegramMiddleware())
    dp.update.outer_middleware(AuthMiddleware())

    logger.info("djgram middlewares setup")


def setup_djgram(
    dp: Dispatcher,
    *,
    add_limiter: bool = True,
    analytics: bool = False,
    dialog_manager_factory: DialogManagerFactory | None = None,
) -> None:
    """
    Установка djgram

    Args:
        dp: диспетчер
        add_limiter: включить лимитер со стандартными настройками
            https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
        analytics: включить сохранение аналитики в ClickHouse
        dialog_manager_factory: фабрика диалоговых менеджеров для aiogram-dialog
    """
    setup_middlewares(dp, analytics=analytics)
    setup_router(dp)
    setup_dialogs(dp, dialog_manager_factory=dialog_manager_factory)

    if add_limiter:
        patch_bot_with_limiter()

    logger.info("djgram setup")
