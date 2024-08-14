from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Update

DEFAULT_ERROR_TEXT_FOR_USER = "Internal error, please contact support"


# pylint: disable=too-few-public-methods
class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Ловит возникающие исключения и сообщает пользователю, что что-то пошло не так
    """

    def __init__(self, error_text: str = DEFAULT_ERROR_TEXT_FOR_USER):
        """
        :param error_text: текст сообщения, отправляемого пользователям при ошибках
        """
        super().__init__()
        self.error_text = error_text

    async def __call__(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:

        try:
            return await handler(update, data)
        except Exception:
            if answer_method := getattr(update.event, "answer", None):
                await answer_method(self.error_text)
            raise
