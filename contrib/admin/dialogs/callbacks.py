"""
Колбеки для диалогов
"""

import logging
from typing import TYPE_CHECKING, Any

from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button

from djgram.contrib.auth.middlewares import MIDDLEWARE_USER_KEY
from djgram.contrib.dialogs.utils import delete_last_message_from_dialog_manager
from djgram.contrib.telegram.middlewares import MIDDLEWARE_TELEGRAM_USER_KEY

from ..rendering import QUERY_KEY
from .states import AdminStates

if TYPE_CHECKING:
    from djgram.contrib.telegram.models import TelegramUser
logger = logging.getLogger(__name__)


def __log_admin_dialog_interaction(middleware_data: dict, action: str) -> None:
    """
    Логирует взаимодействие с диалогом

    Просто общий кусок кода для on_admin_dialog_start и on_admin_dialog_close

    Args:
        middleware_data(dict): данные посредников telegram
        action: действие с диалогом
    """

    telegram_user: TelegramUser = middleware_data[MIDDLEWARE_TELEGRAM_USER_KEY]
    user = middleware_data[MIDDLEWARE_USER_KEY]

    full_name: str = telegram_user.get_full_name()
    logger.info(
        f"{action} admin dialog with user [id={user.id}] "
        f"[telegram_id={telegram_user.id}, username={telegram_user.username}] "
        f"{full_name}",
    )


# pylint: disable=unused-argument
async def on_admin_dialog_start(result: Any, dialog_manager: DialogManager):
    """
    Обработчик начала диалога администрирования

    Просто логирует, что диалог начался
    """
    __log_admin_dialog_interaction(dialog_manager.middleware_data, "Started")


# pylint: disable=unused-argument
async def on_admin_dialog_close(result: Any, dialog_manager: DialogManager):
    """
    Обработчик закрытия диалога администрирования

    Удаляет сообщение администрирования и логирует, что диалог окончен
    """
    __log_admin_dialog_interaction(dialog_manager.middleware_data, "Closed")

    await delete_last_message_from_dialog_manager(dialog_manager)


# pylint: disable=unused-argument
async def on_app_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, app_id: str):
    """
    Обработчик выбора диалога
    """
    manager.dialog_data["app_id"] = int(app_id)
    await manager.switch_to(AdminStates.model_list)


# pylint: disable=unused-argument
async def on_model_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, model_id: str):
    """
    Обработчик выбора модели
    """
    manager.dialog_data["model_id"] = int(model_id)
    await manager.switch_to(AdminStates.row_list)


# pylint: disable=unused-argument
async def on_search_row_input(message: Message, message_input: MessageInput, manager: DialogManager):
    if message.content_type != ContentType.TEXT:
        await message.answer("Поддерживается только поиск по тексту")
        return

    manager.dialog_data[QUERY_KEY] = message.text
    await manager.switch_to(AdminStates.row_list)


# pylint: disable=unused-argument
async def reset_search_query(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data.pop(QUERY_KEY, None)


# pylint: disable=unused-argument
async def on_row_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, row_id: str):
    """
    Обработчик выбора строки
    """
    manager.dialog_data["row_id"] = row_id
    await manager.switch_to(AdminStates.row_detail)


# pylint: disable=unused-argument
async def reset_page(callback: CallbackQuery, widget: Any, manager: DialogManager):
    """
    Сбрасывает текущую страницу
    """

    manager.current_context().widget_data["rows"] = 0
    if QUERY_KEY in manager.dialog_data:
        manager.dialog_data.pop(QUERY_KEY)
