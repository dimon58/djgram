import abc
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from aiogram.enums import ChatAction
from aiogram.types import BufferedInputFile, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender

from djgram.db.models import BaseModel

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

    @abc.abstractmethod
    async def click(self, callback_query: CallbackQuery, obj: BaseModel) -> None:
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

    async def click(self, callback_query: CallbackQuery, obj: BaseModel) -> None:
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

    async def click(self, callback_query: CallbackQuery, obj: BaseModel) -> None:
        if not hasattr(obj, self.file_field):
            logger.error("%s has no attribute %s", obj.__class__, self.file_field)
            return

        file: File = getattr(obj, self.file_field)

        if file is None:
            await callback_query.answer("File is empty")
            return

        async with ChatActionSender(
            bot=callback_query.bot,
            chat_id=callback_query.message.chat.id,
            action=ChatAction.UPLOAD_DOCUMENT,
        ):
            await callback_query.bot.send_document(
                chat_id=callback_query.message.chat.id,
                document=BufferedInputFile(
                    file=file.file.read(),
                    filename=file["filename"],
                ),
            )
