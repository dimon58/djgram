"""
Колбеки для диалогов
"""
from typing import Any

from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput

from ..rendering import QUERY_KEY
from .states import AdminStates


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
