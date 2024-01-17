import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta
from typing import cast

from aiogram.enums import ContentType
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from djgram.configs import ACTIVE_USER_TIMEOUT
from djgram.contrib.admin.filters import make_admin_router
from djgram.contrib.auth.models import User
from djgram.contrib.telegram.models import TelegramChat
from djgram.utils.translation import get_default_word_builder

logger = logging.getLogger(__name__)
router = make_admin_router()

TELEGRAM_BROADCAST_TIMEOUT = 0.05  # limit to 20 messages per second (max = 30)
TELEGRAM_BROADCAST_LOGGING_PERIOD = 5


class BroadcastStatesGroup(StatesGroup):
    wait_message = State()


get_user_word = get_default_word_builder("пользователям", "пользователю", "пользователям")
get_kotoriy_bil_activniy_word = get_default_word_builder(
    "которые были активны", "который был активен", "которые были активны"
)
get_day_word = get_default_word_builder("дней", "день", "дня")
get_week_word = get_default_word_builder("недель", "неделя", "недели")


def get_seconds_word(seconds: int) -> str:
    """
    Возвращает человекочитаемое представление числа секунд

    >>> get_seconds_word(0)
    '0 сек'

    >>> get_seconds_word(123)
    '2 мин 3 сек'

    >>> get_seconds_word(7320)
    '2 ч 2 мин'

    >>> get_seconds_word(86400)
    '1 день'

    >>> get_seconds_word(1209600)
    '2 недели'
    """
    weeks, remainder = divmod(seconds, 7 * 24 * 3600)
    days, remainder = divmod(remainder, 24 * 3600)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    result = []
    if weeks > 0:
        result.append(f"{weeks} {get_week_word(weeks)}")
    if days > 0:
        result.append(f"{days} {get_day_word(days)}")
    if hours > 0:
        result.append(f"{hours} ч")
    if minutes > 0:
        result.append(f"{minutes} мин")
    if seconds > 0 or len(result) == 0:
        result.append(f"{seconds} сек")

    return " ".join(result)


async def send_message(message: Message, chat_id: int, disable_notification: bool = False):
    """
    Safe messages sender

    https://docs.aiogram.dev/en/v2.25.1/examples/broadcast_example.html
    """

    try:
        await message.send_copy(chat_id, disable_notification=disable_notification)

    except TelegramRetryAfter as e:
        logger.warning(f"[BROADCAST] Target [ID:{chat_id}]: Flood limit is exceeded. Sleep {e.retry_after} seconds.")
        await asyncio.sleep(e.retry_after)
        return await send_message(message, chat_id)  # Recursive call

    except TelegramAPIError as exc:
        logger.exception(f"[BROADCAST] Target [ID:{chat_id}]: failed", exc_info=exc)

    else:
        logger.info(f"[BROADCAST] Target [ID:{chat_id}]: success")
        return True

    return False


def apply_active_date_filter(stmt: Select, min_date: datetime) -> Select:
    # noinspection PyTypeChecker
    return stmt.join(User, User.telegram_user_id == TelegramChat.id).where(User.last_interaction >= min_date)


async def broadcast_message(message: Message, db_session: AsyncSession):
    """
    Рассылает копию сообщения всем пользователям из базы данных
    """

    last_interaction_min_date = datetime.now(UTC) - timedelta(seconds=ACTIVE_USER_TIMEOUT)

    # Считаем, сколько нужно разослать
    count_stmt = apply_active_date_filter(
        stmt=select(func.count()).select_from(TelegramChat),
        min_date=last_interaction_min_date,
    )
    count = await db_session.scalar(count_stmt)
    count = cast(int, count)

    if count == 0:
        await message.reply("Некому делать рассылку")
        return

    await message.reply(
        f"Начинаю рассылку {count} {get_user_word(count)}, "
        f"{get_kotoriy_bil_activniy_word(count)} не более, "
        f"чем {get_seconds_word(ACTIVE_USER_TIMEOUT)} назад"
    )

    logging_message_template = (
        "Отправлено {} из {}\nСредняя скорость отправки {:.1f} сообщений/сек\nОсталось около {:.0f} сек"
    )
    logging_message = None

    errors = 0
    chat_id_stmt = apply_active_date_filter(select(TelegramChat.id), last_interaction_min_date)
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

    logging_message = f"Рассылка {count} {get_user_word(count)} завершена за {global_finish - global_start:.1f} сек"

    if errors == 0:
        logging_message += " без ошибок"
    else:
        logging_message += f". Всего ошибок {errors} ({errors / count * 100:.1f}%)."

    await message.reply(logging_message)


# pylint: disable=unused-argument
@router.message(Command("broadcast", "bc"))
async def broadcast_start(message: Message, db_session: AsyncSession, command: CommandObject, state: FSMContext):
    """
    Отправляет сообщения всем пользователям из базы данных

    Можно написать команду вместе с текстовым сообщением или в описании фото, видео, документа и т.д.
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

    await broadcast_message(message, db_session)


@router.message(StateFilter(BroadcastStatesGroup.wait_message))
async def broadcast(message: Message, db_session: AsyncSession, state: FSMContext):
    await broadcast_message(message, db_session)
    await state.clear()
