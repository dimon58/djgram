import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Select

logger = logging.getLogger(__name__)


def get_chat_id_and_last_message_id_from_dialog_manager(dialog_manager: DialogManager) -> tuple[int, int] | None:
    """
    Возвращает кортеж (id чата, id последнего сообщения),
    если есть последнее сообщение, иначе None
    """

    stack = dialog_manager.current_stack()

    if (
        isinstance(dialog_manager.event, CallbackQuery)
        and dialog_manager.event.message
        and stack.last_message_id == dialog_manager.event.message.message_id
    ):
        return dialog_manager.event.message.chat.id, dialog_manager.event.message.message_id

    if not stack or not stack.last_message_id:
        return None

    # Реально сюда передаётся экземпляр класса ManagerImpl
    # noinspection PyProtectedMember

    chat_id = dialog_manager._data["event_chat"].id  # noqa: SLF001 # pyright: ignore [reportAttributeAccessIssue]
    return chat_id, stack.last_message_id


async def remove_kbd(bot: Bot, chat_id: int | None, message_id: int | None) -> Message | None:
    """
    Удаляет inline клавиатуру у сообщения
    """
    if not message_id:
        logger.debug("remove kbd in chat %s fail: message id is None", chat_id)
        return
    try:
        await bot.edit_message_reply_markup(
            message_id=message_id,
            chat_id=chat_id,
        )
        logger.debug("removed kbd in chat %s", chat_id)
    except TelegramBadRequest as exc:
        logger.debug("remove kbd in chat %s fail: %s", chat_id, exc.message)
        if (
            "message is not modified" in exc.message  # nothing to remove
            or "message can't be edited" in exc.message
            or "message to edit not found" in exc.message
        ):
            pass
        else:
            raise


async def delete_message_safe(bot: Bot, chat_id: int, message_id: int) -> None:
    """
    Безопасно удаляет сообщение, если не получается, то удаляет хотя бы inline клавиатуру
    """
    try:
        await bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )
        logger.debug("deleted message %s in chat %s", message_id, chat_id)
    except TelegramBadRequest as exc:
        logger.debug("failed to delete message %s in chat %s: %s", message_id, chat_id, exc.message)
        if "message to delete not found" in exc.message or "message can't be deleted" in exc.message:
            await remove_kbd(bot, chat_id, message_id)
        else:
            raise


async def delete_last_message_from_dialog_manager(dialog_manager: DialogManager) -> None:
    """
    Удаляет последние сообщение в диалоге, описываемом dialog_manager
    """
    res = get_chat_id_and_last_message_id_from_dialog_manager(dialog_manager)
    if res is None:
        return

    chat_id, message_id = res

    await delete_message_safe(
        bot=dialog_manager.middleware_data["bot"],
        chat_id=chat_id,
        message_id=message_id,
    )


def set_value_and_switch_to(key: str, next_state: State):
    async def on_click(callback: CallbackQuery, widget: Select, manager: DialogManager, value: str) -> None:
        old_value = manager.dialog_data.get(key)
        manager.dialog_data[key] = value

        logger.debug("Changed dialog data for %s (%s: %s -> %s)", manager.current_context().id, key, old_value, value)
        await manager.switch_to(next_state)

    return on_click
