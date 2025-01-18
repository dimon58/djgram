from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import CancelHandler, SkipHandler
from aiogram.types import Update

from djgram.system_configs import DEFAULT_ERROR_TEXT_FOR_USER


# pylint: disable=too-few-public-methods
class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Ловит возникающие исключения и сообщает пользователю, что что-то пошло не так

    Аналог aiogram.dispatcher.middlewares.error.ErrorsMiddleware
    """

    def __init__(
        self,
        error_text: str = DEFAULT_ERROR_TEXT_FOR_USER,
        skip_exceptions: type(Exception) | tuple[type(Exception), ...] = (),
    ):
        """
        :param error_text: текст сообщения, отправляемого пользователям при ошибках
        """
        super().__init__()
        self.error_text = error_text
        self.skip_exceptions = (SkipHandler, CancelHandler, *skip_exceptions)

    async def __call__(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(update, data)
        except self.skip_exceptions:  # pragma: no cover
            raise
        except Exception:
            if answer_method := getattr(update.event, "answer", None):
                await answer_method(self.error_text)
            raise
