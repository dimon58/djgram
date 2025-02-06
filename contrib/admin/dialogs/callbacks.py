"""
Колбеки для диалогов
"""

import logging
from typing import Any

from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from djgram.contrib.dialogs.utils import delete_last_message_from_dialog_manager

from ..misc import get_admin_representation_for_logging_from_middleware_data
from ..rendering import QUERY_KEY
from . import getters
from .getters import PAGE_KEY
from .states import AdminStates

logger = logging.getLogger(__name__)


def __log_admin_dialog_interaction(middleware_data: dict, action: str) -> None:
    """
    Логирует взаимодействие с диалогом

    Просто общий кусок кода для on_admin_dialog_start и on_admin_dialog_close

    Args:
        middleware_data(dict): данные посредников telegram
        action: действие с диалогом
    """

    logger.info(
        "%s admin dialog with user %s",
        action,
        get_admin_representation_for_logging_from_middleware_data(middleware_data),
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
    manager.dialog_data[getters.APP_ID_KEY] = int(app_id)
    await manager.switch_to(AdminStates.model_list)


# pylint: disable=unused-argument
async def on_model_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, model_id: str):
    """
    Обработчик выбора модели
    """
    manager.current_context().widget_data[PAGE_KEY] = 0
    manager.dialog_data[getters.MODEL_ID_KEY] = int(model_id)
    await manager.switch_to(AdminStates.row_list)


# pylint: disable=unused-argument
async def on_search_row_input(message: Message, message_input: MessageInput, manager: DialogManager):
    if message.content_type != ContentType.TEXT:
        await message.answer("Поддерживается только поиск по тексту")
        return

    manager.current_context().widget_data[PAGE_KEY] = 0
    manager.dialog_data[QUERY_KEY] = message.text
    await manager.switch_to(AdminStates.row_list)


# pylint: disable=unused-argument
async def reset_search_query(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    manager.current_context().widget_data[PAGE_KEY] = 0
    manager.dialog_data.pop(QUERY_KEY, None)


# pylint: disable=unused-argument
async def on_row_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, row_id: str):
    """
    Обработчик выбора строки
    """
    manager.dialog_data[getters.ROW_ID_KEY] = row_id
    await manager.switch_to(AdminStates.row_detail)


# pylint: disable=unused-argument
async def reset_page(callback: CallbackQuery, widget: Any, manager: DialogManager):
    """
    Сбрасывает текущую страницу
    """

    manager.current_context().widget_data[getters.ROWS_KEY] = 0
    if QUERY_KEY in manager.dialog_data:
        manager.dialog_data.pop(QUERY_KEY)


async def handle_object_action_button(
    callback_query: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    object_action_button_id: str,
):
    """
    Обрабатывает нажатия на кнопки действия для записей в бд
    """
    _, model, model_admin, obj, row_id = await getters.get_admin_object_detail_context(manager)

    if obj is None:
        logger.error("Not found %s with id = %s", model, row_id)
        return

    object_action_button = model_admin.get_object_action_button_by_id(object_action_button_id)

    if object_action_button is None:
        logger.error("Failed to find object action button id=%s in %s", object_action_button_id, model_admin)
        return

    logger.info(
        "Admin %s clicked on object action button id=%s (%s) for object %s",
        get_admin_representation_for_logging_from_middleware_data(manager.middleware_data),
        object_action_button_id,
        object_action_button.get_title(obj),
        obj,
    )
    await object_action_button.click(obj, callback_query, manager.middleware_data)
