import abc
import json
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import pydantic
from aiogram.enums import ChatAction
from aiogram.types import BufferedInputFile, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender

from djgram.db.models import BaseModel
from djgram.system_configs import MIDDLEWARE_AUTH_USER_KEY, MIDDLEWARE_TELEGRAM_USER_KEY
from djgram.utils.formating import get_bytes_size_format
from djgram.utils.misc import measure_time

from .misc import get_admin_representation_for_logging

if TYPE_CHECKING:
    from sqlalchemy_file import File

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class AbstractObjectActionButton(abc.ABC, Generic[T]):
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

    # noinspection PyMethodMayBeStatic
    def should_render(self, obj: T, middleware_data: dict[str, Any]) -> bool:
        """
        Нужно ли рендерить кнопку

        Может быть переопределено для кастомного поведения

        #todo интеграция с magic filter (F)
        """
        return True

    def get_title(self, obj: T) -> str:
        """
        Возвращает название кнопки с учётом конкретного объекта

        Можно переопределить
        """
        return self.title

    @abc.abstractmethod
    async def click(self, obj: T, callback_query: CallbackQuery, middleware_data: dict[str, Any]) -> None:
        """
        Обработчик нажатия на кнопку

        :param callback_query: callback query из bot api
        :param obj: запись в бд для которой нажимается кнопка
        """


class CallbackObjectActionButton(AbstractObjectActionButton[T]):
    """
    Кнопка выполняющая переданный колбек при нажатии
    """

    def __init__(self, button_id: str, title: str, callback: Callable[[CallbackQuery, T], Awaitable[None]]):
        """
        :param callback: колбек при нажатии на кнопку
        """
        super().__init__(button_id, title)
        self.callback = callback

    async def click(self, obj: T, callback_query: CallbackQuery, middleware_data: dict[str, Any]) -> None:
        await self.callback(callback_query, obj)


class DownloadFileActionButton(AbstractObjectActionButton[T]):
    """
    Отправляет файл при нажатии
    """

    def __init__(
        self,
        button_id: str,
        title: str,
        field_name: str,
        on_empty_message_text: str = "File is empty",
        filename: str | None = None,
    ):
        """
        :param field_name: название поля с файлом из sqlalchemy_file
        """
        super().__init__(button_id, title)
        self.field_name = field_name
        self.on_empty_message_text = on_empty_message_text
        self.filename = filename

    async def click(self, obj: T, callback_query: CallbackQuery, middleware_data: dict[str, Any]) -> None:
        if not hasattr(obj, self.field_name):
            logger.error("%s has no attribute %s", obj.__class__, self.field_name)
            return

        file: File = getattr(obj, self.field_name)

        if file is None:
            await callback_query.answer(self.on_empty_message_text)
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
                        filename=self.filename or file["filename"],
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


class DownloadStringAsFileActionButton(DownloadFileActionButton[T]):
    def __init__(  # noqa: D107
        self,
        button_id: str,
        title: str,
        field_name: str,
        filename: str | None = None,
        on_empty_message_text: str = "Text is empty",
        default_ext: str = "txt",
    ):
        super().__init__(
            button_id=button_id,
            title=title,
            field_name=field_name,
            filename=filename,
            on_empty_message_text=on_empty_message_text,
        )
        self.default_ext = default_ext

    def prepare_field_content(self, field_content: Any) -> bytes:
        return field_content.encode("utf8")

    async def click(self, obj: T, callback_query: CallbackQuery, middleware_data: dict[str, Any]) -> None:
        if not hasattr(obj, self.field_name):
            logger.error("%s has no attribute %s", obj.__class__, self.field_name)
            return

        field_content = getattr(obj, self.field_name)

        if field_content is None:
            await callback_query.answer(self.on_empty_message_text)
            return

        field_content = self.prepare_field_content(field_content)

        logger.info(
            "Sending content from field %s from %s to admin %s",
            self.field_name,
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
                        file=field_content,
                        filename=self.filename or f"{self.field_name}.{self.default_ext}",
                    ),
                )

        file_size = len(field_content)
        logger.info(
            "Data from field %s from %s with size %s successfully sent in %.2f sec (avg %s/s) "
            "to admin %s in message %s (telegram file id = %s)",
            self.field_name,
            obj,
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


class DownloadJsonActionButton(DownloadStringAsFileActionButton[T]):
    """
    Отправляет json в виде файла при нажатии
    """

    def __init__(
        self,
        button_id: str,
        title: str,
        field_name: str,
        filename: str | None = None,
        on_empty_message_text: str = "Json is empty",
        default_ext: str = "json",
    ):
        """
        :param field_name: название поля с json из sqlalchemy_file
        """
        super().__init__(
            button_id=button_id,
            title=title,
            field_name=field_name,
            filename=filename,
            on_empty_message_text=on_empty_message_text,
            default_ext=default_ext,
        )

    def prepare_field_content(self, field_content: Any) -> bytes:
        if isinstance(field_content, pydantic.BaseModel):
            return field_content.model_dump_json(indent=2).encode("utf8")
        if isinstance(field_content, dict):
            return json.dumps(field_content, indent=2, ensure_ascii=False).encode("utf8")
        raise TypeError(f"Type {field_content.__class__.__name__} not supported")
