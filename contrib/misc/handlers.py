from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram_dialog import DialogManager


async def cancel_handler(message: Message, state: FSMContext, dialog_manager: DialogManager):
    """
    Команда сброса состояния
    """

    if (await state.get_state()) is not None or dialog_manager.has_context():
        await state.clear()
        await dialog_manager.reset_stack()
        msg = "Действие отменено"
    else:
        msg = "Нечего отменять"

    await message.answer(text=msg, reply_markup=ReplyKeyboardRemove())
