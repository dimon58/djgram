"""
Колбеки для диалогов
"""
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

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
async def on_row_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, row_id: str):
    """
    Обработчик выбора строки
    """
    manager.dialog_data["row_id"] = int(row_id)
    await manager.switch_to(AdminStates.row_detail)


# pylint: disable=unused-argument
async def reset_page(callback: CallbackQuery, widget: Any, manager: DialogManager):
    """
    Сбрасывает текущую страницу
    """

    manager.current_context().widget_data["rows"] = 0
