from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram_dialog import DialogManager


async def cancel_handler(message: Message, state: FSMContext, dialog_manager: DialogManager) -> None:
    """
    Команда сброса состояния
    """

    has_context = dialog_manager.has_context()
    if has_context or (await state.get_state()):
        await state.clear()
        await dialog_manager.reset_stack()
        msg = "Действие отменено"
    else:
        msg = "Нечего отменять"

    await message.answer(text=msg, reply_markup=ReplyKeyboardRemove())
