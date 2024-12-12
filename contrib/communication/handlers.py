import logging

from aiogram.enums import ContentType
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from djgram.contrib.admin.filters import make_admin_router
from djgram.contrib.communication.broadcast import broadcast_message

logger = logging.getLogger(__name__)
router = make_admin_router()


class BroadcastStatesGroup(StatesGroup):
    wait_message = State()


# pylint: disable=unused-argument
@router.message(Command("broadcast", "bc"))
async def broadcast_start(message: Message, db_session: AsyncSession, command: CommandObject, state: FSMContext):
    """
    Отправляет сообщения всем активным пользователям из базы данных

    Можно написать команду вместе с текстовым сообщением или в описании фото, видео, документа и т.д.

    Если отправлена только команда, то следующим сообщением ждет сообщения для рассылки
    """

    # Если отправлена просто команда, то ждём следующее сообщение для рассылки
    if command.args is None and message.content_type == ContentType.TEXT:
        await message.answer("Отправьте сообщение, которое нужно разослать всем\n\nОтменить отправку - /cancel")
        await state.set_state(BroadcastStatesGroup.wait_message)
        return

    # Удаляем команду в начале сообщения
    message.model_config["frozen"] = False
    if message.text:
        # noinspection Pydantic
        message.text = command.args

    elif message.caption:
        # noinspection Pydantic
        message.caption = command.args
    message.model_config["frozen"] = True

    await broadcast_message(message, db_session, message)


@router.message(StateFilter(BroadcastStatesGroup.wait_message))
async def broadcast(message: Message, db_session: AsyncSession, state: FSMContext) -> None:
    await broadcast_message(message, db_session, message)
    await state.clear()
