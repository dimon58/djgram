import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Update

from djgram.db import async_session_maker

MIDDLEWARE_DB_SESSION_KEY = "db_session"

logger = logging.getLogger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    """
    Добавляет сессию к базе данных в аргумент db_session

    https://docs.aiogram.dev/en/dev-3.x/dispatcher/middlewares.html#arguments-specification
    """

    async def __call__(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:
        async with async_session_maker() as db_session:
            await db_session.begin()

            data[MIDDLEWARE_DB_SESSION_KEY] = db_session

            result = await handler(update, data)

            await db_session.commit()

            return result
