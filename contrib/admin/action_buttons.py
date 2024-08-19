import abc
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiogram.enums import ChatAction
from aiogram.types import BufferedInputFile, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender

from djgram.db.models import BaseModel
from djgram.system_configs import MIDDLEWARE_AUTH_USER_KEY, MIDDLEWARE_TELEGRAM_USER_KEY
from djgram.utils import measure_time
from djgram.utils.formating import get_bytes_size_format

from .misc import get_admin_representation_for_logging

if TYPE_CHECKING:
    from sqlalchemy_file import File


logger = logging.getLogger(__name__)


class AbstractObjectActionButton(abc.ABC):
    """
    Базовый класс кнопки действия над объектом в админке

    Отображается под текстом
    """

    def __init__(self, button_id: str, title: str):
        """
        :param button_id: id кнопки в реестре
        :param title: надпись на кнопке
        """
        self.button_id = button_id
        self.title = title

    def get_title(self, obj: BaseModel) -> str:
        """
        Возвращает название кнопки с учётом конкретного объекта

        Можно переопределить
        """
        return self.title

    @abc.abstractmethod
    async def click(self, obj: BaseModel, callback_query: CallbackQuery, middleware_data: dict[str, Any]) -> None:
        """
        Обработчик нажатия на кнопку

        :param callback_query: callback query из bot api
        :param obj: запись в бд для которой нажимается кнопка
        """


class CallbackObjectActionButton(AbstractObjectActionButton):
    """
    Кнопка выполняющая переданный колбек при нажатии
    """

    def __init__(self, button_id: str, title: str, callback: Callable[[CallbackQuery, BaseModel], Awaitable[None]]):
        """
        :param callback: колбек при нажатии на кнопку
        """
        super().__init__(button_id, title)
        self.callback = callback

    async def click(self, obj: BaseModel, callback_query: CallbackQuery, middleware_data: dict[str, Any]) -> None:
        await self.callback(callback_query, obj)


class DownloadFileActionButton(AbstractObjectActionButton):
    """
    Отправляет файл при нажатии
    """

    def __init__(self, button_id: str, title: str, file_field: str):
        """
        :param file_field: название поля с файлом из sqlalchemy_file
        """
        super().__init__(button_id, title)
        self.file_field = file_field

    async def click(self, obj: BaseModel, callback_query: CallbackQuery, middleware_data: dict[str, Any]) -> None:
        if not hasattr(obj, self.file_field):
            logger.error("%s has no attribute %s", obj.__class__, self.file_field)
            return

        file: File = getattr(obj, self.file_field)

        if file is None:
            await callback_query.answer("File is empty")
            return

        logger.info(
            "Sending file %s (id=%s) from %s to admin %s",
            file["filename"],
            file["file_id"],
            obj,
            get_admin_representation_for_logging(
                telegram_user=middleware_data[MIDDLEWARE_TELEGRAM_USER_KEY],
                user=middleware_data[MIDDLEWARE_AUTH_USER_KEY],
            ),
        )
        async with ChatActionSender(
            bot=callback_query.bot,  # pyright: ignore [reportArgumentType]
            chat_id=callback_query.message.chat.id,  # pyright: ignore [reportOptionalMemberAccess]
            action=ChatAction.UPLOAD_DOCUMENT,
        ):
            with measure_time() as td:
                message = await callback_query.bot.send_document(  # pyright: ignore [reportOptionalMemberAccess]
                    chat_id=callback_query.message.chat.id,  # pyright: ignore [reportOptionalMemberAccess]
                    document=BufferedInputFile(
                        file=file.file.read(),
                        filename=file["filename"],
                    ),
                )

        file_size = file["size"]
        logger.info(
            "File from %s %s (id=%s) with size %s successfully sent in %.2f sec (avg %s/s) "
            "to admin %s in message %s (telegram file id = %s)",
            obj,
            file["filename"],
            file["file_id"],
            get_bytes_size_format(file_size),
            td.elapsed,
            get_bytes_size_format(file_size / td.elapsed),
            get_admin_representation_for_logging(
                telegram_user=middleware_data[MIDDLEWARE_TELEGRAM_USER_KEY],
                user=middleware_data[MIDDLEWARE_AUTH_USER_KEY],
            ),
            message.message_id,
            message.document.file_id,  # pyright: ignore [reportOptionalMemberAccess]
        )
