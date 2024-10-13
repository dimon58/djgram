"""
Действия после валидации ввода в FormInput
"""

from collections.abc import Hashable, Sequence
from typing import TYPE_CHECKING, Any, cast

from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.kbd.button import OnClick

from .utils import set_value_using_composite_key
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


def set_value(
    key: Hashable | Sequence[Hashable],
    value: Any,
    next_state: State | None = None,
    **next_state_kwargs,
) -> OnClick:
    """
    Устанавливает данные диалога
    """
    if isinstance(key, str):
        key = [key]

    async def inner(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
        set_value_using_composite_key(
            data=manager.dialog_data,
            key=cast(Sequence[Hashable], key),
            value=value,
        )

        if next_state is not None:
            if next_state.group == manager.current_context().state.group:
                await manager.switch_to(next_state, **next_state_kwargs)
            else:
                await manager.switch_to(next_state, **next_state_kwargs)

    return inner
