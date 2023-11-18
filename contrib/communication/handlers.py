import asyncio
import logging
import time

from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.filters import Command, MagicData, CommandObject
from aiogram.types import Message
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from djgram.contrib.telegram.models import TelegramChat

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(MagicData(F.user.is_admin))

TELEGRAM_BROADCAST_TIMEOUT = 0.05  # limit to 20 messages per second (max = 30)
TELEGRAM_BROADCAST_LOGGING_PERIOD = 5


def get_chat_word(number: int) -> str:
    """
    0 чатов
    1 чат
    2 чата
    3 чата
    4 чата
    5 чатов
    6 чатов
    7 чатов
    8 чатов
    9 чатов
    10 чатов
    11 чатов
    12 чатов
    13 чатов
    14 чатов
    15 чатов
    16 чатов
    17 чатов
    18 чатов
    19 чатов
    20 чатов
    21 чат
    ...
    """
    number %= 100
    if 5 <= number <= 20:
        return "чатов"

    number %= 10

    if number == 1:
        return "чат"

    if 2 <= number <= 4:
        return "чата"

    return "чатов"


async def send_message(message: Message, chat_id: int, disable_notification: bool = False):
    """
    Safe messages sender

    https://docs.aiogram.dev/en/v2.25.1/examples/broadcast_example.html
    """

    try:
        await message.send_copy(chat_id, disable_notification=disable_notification)

    except TelegramRetryAfter as e:
        logger.warning(f"Target [ID:{chat_id}]: Flood limit is exceeded. Sleep {e.retry_after} seconds.")
        await asyncio.sleep(e.retry_after)
        return await send_message(message, chat_id)  # Recursive call

    except TelegramAPIError as exc:
        logger.exception(f"Target [ID:{chat_id}]: failed", exc_info=exc)

    else:
        logger.info(f"Target [ID:{chat_id}]: success")
        return True

    return False


# pylint: disable=unused-argument
@router.message(Command("broadcast", "bc"))
async def broadcast(message: Message, db_session: AsyncSession, command: CommandObject):
    """
    Отправляет сообщения всем пользователям из базы данных

    Можно написать команду вместе с текстовым сообщением или в описании фото, видео, документа и т.д.
    """

    # Игнорируем пустое сообщение
    if command.args is None and message.content_type == ContentType.TEXT:
        await message.answer("Нельзя разослать пустое сообщение")
        return

    # Удаляем команду в начале сообщения
    message.model_config["frozen"] = False
    if message.text:
        message.text = command.args

    elif message.caption:
        message.caption = command.args
    message.model_config["frozen"] = True

    # Считаем, сколько нужно разослать
    count_stmt = select(func.count("*")).select_from(TelegramChat)
    count = await db_session.scalar(count_stmt)
    await message.reply(f"Начинаю рассылку в {count} {get_chat_word(count)}")

    logging_message_template = (
        "Отправлено {} из {}\n" "Средняя скорость отправки {:.1f} сообщений/сек\n" "Осталось около {:.0f} сек"
    )
    logging_message = None

    errors = 0
    chat_id_stmt = select(TelegramChat.id)
    last_logging_time = start = global_start = time.perf_counter()
    for number, chat_id in enumerate((await db_session.scalars(chat_id_stmt)).yield_per(1000), start=1):
        try:
            success = await send_message(message, chat_id)
        except RecursionError as exc:
            logger.exception(exc)
        else:
            if not success:
                errors += 1

        finish = time.perf_counter()
        if (finish - start) < TELEGRAM_BROADCAST_TIMEOUT:
            await asyncio.sleep(TELEGRAM_BROADCAST_TIMEOUT - finish + start)

        # Логируем, сколько уже отправлено сообщений
        if (finish - last_logging_time) > TELEGRAM_BROADCAST_LOGGING_PERIOD:
            avg_speed = number / (finish - global_start)
            time_left = (count - number) / avg_speed
            text = logging_message_template.format(number, count, avg_speed, time_left)
            if logging_message is None:
                logging_message = await message.reply(text)
            else:
                try:
                    await logging_message.edit_text(text)
                except TelegramAPIError:
                    logging_message = await message.reply(text)
            last_logging_time = finish

        start = finish
    global_finish = time.perf_counter()

    logging_message = f"Рассылка в {count} {get_chat_word(count)} завершена за {global_finish - global_start:.1f} сек"

    if errors == 0:
        logging_message += " без ошибок"
    else:
        logging_message += f". Всего ошибок {errors} ({errors / count * 100:.1f}%)."

    await message.reply(logging_message)
