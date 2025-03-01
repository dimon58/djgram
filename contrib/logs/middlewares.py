from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Update

from .context import UPDATE_ID


class TraceMiddleware(BaseMiddleware):
    """
    Записывает в контекст логгера update_id
    """

    async def __call__(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:
        UPDATE_ID.set(update.update_id)
        result = await handler(update, data)
        UPDATE_ID.set(None)

        return result
