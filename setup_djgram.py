import logging

from aiogram import Dispatcher
from aiogram.dispatcher.middlewares.user_context import UserContextMiddleware
from aiogram.filters import Command
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.internal import DialogManagerFactory

from djgram.contrib.admin import router as admin_router
from djgram.contrib.analytics.bot_answer_analytics import setup_bot_answer_analytics
from djgram.contrib.analytics.dialog_analytics import setup_dialog_analytics
from djgram.contrib.analytics.middlewares import (
    DialogAnalyticsInnerCallbackQueryMiddleware,
    DialogAnalyticsInnerMessageMiddleware,
    SaveUpdateToClickHouseMiddleware,
)
from djgram.contrib.auth.middlewares import AuthMiddleware
from djgram.contrib.communication import router as communication_router
from djgram.contrib.limits.limiter import patch_bot_with_limiter
from djgram.contrib.logs.middlewares import TraceMiddleware
from djgram.contrib.misc.handlers import cancel_handler
from djgram.contrib.misc.middlewares import ErrorHandlingMiddleware
from djgram.contrib.telegram.middlewares import TelegramMiddleware
from djgram.db.middlewares import DbSessionMiddleware
from djgram.system_configs import DEFAULT_ERROR_TEXT_FOR_USER

logger = logging.getLogger(__name__)


def setup_router(dp: Dispatcher) -> None:
    dp.message.register(cancel_handler, Command("cancel"))
    dp.include_router(communication_router)
    dp.include_router(admin_router)

    logger.info("djgram routers setup")


def setup_middlewares(
    dp: Dispatcher,
    *,
    analytics: bool,
    error_text: str,
    skip_exceptions: type[Exception] | tuple[type[Exception], ...],
) -> None:
    dp.update.outer_middleware(TraceMiddleware())
    dp.update.outer_middleware(ErrorHandlingMiddleware(error_text, skip_exceptions))
    dp.update.outer_middleware(UserContextMiddleware())
    if analytics:
        dp.update.outer_middleware(SaveUpdateToClickHouseMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(TelegramMiddleware())
    dp.update.outer_middleware(AuthMiddleware())

    logger.info("djgram middlewares setup")


def setup_djgram(  # noqa: PLR0913
    dp: Dispatcher,
    *,
    add_limiter: bool = True,
    analytics: bool = False,
    error_text: str = DEFAULT_ERROR_TEXT_FOR_USER,
    skip_exceptions: type[Exception] | tuple[type[Exception], ...] = (),
    dialog_manager_factory: DialogManagerFactory | None = None,
) -> None:
    """
    Установка djgram

    Args:
        dp: диспетчер
        add_limiter: включить лимитер со стандартными настройками
            https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
        analytics: включить сохранение аналитики в ClickHouse
        error_text: текст сообщения, которое будет отправляться пользователями при ошибках в системе
        skip_exceptions: список исключений, который не нужно обрабатывать в ErrorHandlingMiddleware
        dialog_manager_factory: фабрика диалоговых менеджеров для aiogram-dialog
    """
    setup_middlewares(dp, analytics=analytics, error_text=error_text, skip_exceptions=skip_exceptions)
    setup_router(dp)
    setup_dialogs(dp, dialog_manager_factory=dialog_manager_factory)

    if add_limiter:
        patch_bot_with_limiter()

    if analytics:
        setup_dialog_analytics()
        setup_bot_answer_analytics()

        dp.message.middleware(DialogAnalyticsInnerMessageMiddleware())
        dp.callback_query.middleware(DialogAnalyticsInnerCallbackQueryMiddleware())

    logger.info("djgram setup")
