import copy
import time
from typing import TYPE_CHECKING

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram_dialog import DialogManager
from aiogram_dialog.api.internal import CONTEXT_KEY, STACK_KEY
from aiogram_dialog.widgets.input import MessageInput

from djgram.contrib.analytics import dialog_analytics

if TYPE_CHECKING:
    from aiogram_dialog.api.entities import Context, Stack


async def cancel_handler(message: Message, state: FSMContext, dialog_manager: DialogManager) -> None:
    """
    Команда сброса состояния
    """

    has_context = dialog_manager.has_context()
    if has_context or (await state.get_state()):

        if has_context and dialog_analytics.DIALOG_ANALYTICS_ENABLED:
            aiogd_context_before: Context = copy.deepcopy(dialog_manager.middleware_data[CONTEXT_KEY])
            aiogd_stack_before: Stack = copy.deepcopy(dialog_manager.middleware_data[STACK_KEY])
            start = time.perf_counter()

        await state.clear()
        await dialog_manager.reset_stack()

        if has_context and dialog_analytics.DIALOG_ANALYTICS_ENABLED:
            end = time.perf_counter()
            # noinspection PyUnboundLocalVariable
            await dialog_analytics.save_input_statistics(
                processor="cancel_handler",
                processed=True,
                process_time=end - start,
                not_processed_reason=None,
                input_=MessageInput(None),
                message=message,
                middleware_data=dialog_manager.middleware_data,
                aiogd_context_before=aiogd_context_before,
                aiogd_stack_before=aiogd_stack_before,
            )

        msg = "Действие отменено"
    else:
        msg = "Нечего отменять"

    await message.answer(text=msg, reply_markup=ReplyKeyboardRemove())
