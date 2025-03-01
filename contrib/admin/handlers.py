"""
Обработчики
"""

import logging

from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from .dialogs import admin_dialog
from .dialogs.states import AdminStates
from .filters import make_admin_router

logger = logging.getLogger(__name__)
router = make_admin_router()
router.include_router(admin_dialog)


@router.message(Command(commands=["admin"]))
async def admin(message: Message, dialog_manager: DialogManager):
    """
    Запуск диалога администрирования
    """

    await dialog_manager.start(AdminStates.app_list, mode=StartMode.RESET_STACK)
