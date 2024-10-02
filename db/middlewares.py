import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Update

from djgram.db.base import get_autocommit_session
from djgram.system_configs import MIDDLEWARE_DB_SESSION_KEY

logger = logging.getLogger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    """
    Добавляет сессию к базе данных в аргумент db_session

    https://docs.aiogram.dev/en/dev-3.x/dispatcher/middlewares.html#arguments-specification
    """

    def __init__(self, *, commit_on_end: bool = True):
        """
        Args:
            commit_on_end: Нужно ли коммитить при окончании сессии
        """
        self.commit_on_end = commit_on_end

    async def __call__(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:
        async with get_autocommit_session(commit_on_end=self.commit_on_end) as db_session:
            data[MIDDLEWARE_DB_SESSION_KEY] = db_session

            return await handler(update, data)
