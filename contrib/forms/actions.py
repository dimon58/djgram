"""
Действия после валидации ввода в FormInput
"""

from typing import TYPE_CHECKING

from aiogram.fsm.state import State
from aiogram.types import Message
from aiogram_dialog import DialogManager

from .validators import FormInputValidationCallback

if TYPE_CHECKING:
    from .inputs import FormInput


def send_text(text: str) -> FormInputValidationCallback:
    """
    Отправляет текст
    """

    async def inner(message: Message, form_input: "FormInput", manager: DialogManager) -> None:
        await message.answer(text)

    return inner


def switch_to(state: State) -> FormInputValidationCallback:
    """
    Переключает на другое состояние
    """

    async def inner(message: Message, form_input: "FormInput", manager: DialogManager) -> None:
        await manager.switch_to(state)

    return inner
