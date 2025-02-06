import asyncio
import enum
import logging
import time
from collections.abc import Awaitable, Callable, Iterable
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import Message
from djgram.configs import (
    ACTIVE_USER_TIMEOUT,
    TELEGRAM_BROADCAST_LOGGING_PERIOD,
    TELEGRAM_BROADCAST_TIMEOUT,
)
from djgram.contrib.auth.models import User
from djgram.contrib.telegram.models import TelegramChat
from djgram.utils.formating import get_default_word_builder, seconds_to_human_readable
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


get_kotoriy_bil_activniy_word = get_default_word_builder(
    "которые были активны",
    "который был активен",
    "которые были активны",
)
get_user_word = get_default_word_builder("пользователям", "пользователю", "пользователям")


class SendMessageStatus(enum.Enum):
    """
    Статусы отправки сообщения
    """

    SUCCESS = "success"
    BLOCKED = "blocked"
    FAIL = "fail"


async def broadcast(  # noqa: C901, PLR0912, PLR0913, PLR0915
    send_method: Callable[..., Awaitable[Any]],
    chat_ids: Iterable[int],
    count: int,
    logging_message: Message | None = None,
    broadcast_timeout: float = TELEGRAM_BROADCAST_TIMEOUT,
    logging_period: float = TELEGRAM_BROADCAST_LOGGING_PERIOD,
    per_chat_kwargs: Iterable[dict[str, Any]] | None = None,
    **kwargs,
) -> int:
    """
    Массово отправляет сообщение для пользователей

    Args:
        send_method: Метод для отправки сообщений, в который можно передать чат id. Например: Bot.send_message
        chat_ids: итерируемая последовательность id чатов для отправки
        count: длина последовательности
        logging_message: сообщение, в ответ на которое будут приходить логи о статусе выполнения отправки
        broadcast_timeout: минимальное время межу отправкой сообщений
        logging_period: минимальный период логирования
        per_chat_kwargs: дополнительные параметры для send_method для каждого отельного чата
        kwargs: дополнительные параметры для send_method. Например, для Bot.send_message нужно указать text

    Returns:
        int: число ошибок отправки
    """
    status_message_template = (
        "Отправлено {} из {}\nСредняя скорость отправки {:.1f} сообщений/сек\nОсталось около {:.0f} сек"
    )
    status_message = None

    logger.info("Started broadcast to %s users", count)
    errors = 0
    blocked = 0
    if per_chat_kwargs:
        per_chat_kwargs = iter(per_chat_kwargs)
    last_logging_time = start = global_start = time.perf_counter()
    for number, chat_id in enumerate(chat_ids, start=1):
        chat_kwargs = (
            next(per_chat_kwargs) if per_chat_kwargs is not None else {}  # pyright: ignore [reportArgumentType]
        )

        try:
            status = await send_method(chat_id=chat_id, **chat_kwargs, **kwargs)
        except RecursionError as exc:
            logger.exception("Too many attempts to send message", exc_info=exc)
            errors += 1
        else:
            if status == SendMessageStatus.FAIL:
                errors += 1
            elif status == SendMessageStatus.BLOCKED:
                blocked += 1

        finish = time.perf_counter()
        if (finish - start) < broadcast_timeout:
            await asyncio.sleep(broadcast_timeout - finish + start)

        # Логируем, сколько уже отправлено сообщений
        if (finish - last_logging_time) > logging_period:
            avg_speed = number / (finish - global_start)
            time_left = (count - number) / avg_speed
            text = status_message_template.format(number, count, avg_speed, time_left)
            last_logging_time = finish

            # Само логирование
            logger.info(text)
            if logging_message is not None:
                if status_message is None:
                    status_message = await logging_message.reply(text)
                else:
                    try:
                        await status_message.edit_text(text)
                    except TelegramAPIError:
                        status_message = await logging_message.reply(text)

        start = finish
    global_finish = time.perf_counter()

    status_message = f"Рассылка {count} {get_user_word(count)} завершена за {global_finish - global_start:.1f} сек"
    if errors == 0:
        status_message += " без ошибок"
    else:
        status_message += f". Всего ошибок {errors} ({errors / count * 100:.1f}%)."

    if blocked > 0:
        if errors == 0:
            status_message += "."
        status_message += f" Не удалось отправить из-за блокировки {blocked} ({blocked / count * 100:.1f}%)."

    logger.info(status_message)
    if logging_message is not None:
        await logging_message.reply(status_message)

    return errors


async def send_message_copy(
    message: Message,
    chat_id: int | str,
    *,
    disable_notification: bool = False,
) -> SendMessageStatus:
    """
    Safe messages sender

    https://docs.aiogram.dev/en/v2.25.1/examples/broadcast_example.html
    """

    try:
        await message.send_copy(chat_id, disable_notification=disable_notification)

    except TelegramRetryAfter as e:
        logger.warning(
            "[BROADCAST] Target [ID:%s]: Flood limit is exceeded. Sleep %s seconds.",
            chat_id,
            e.retry_after,
        )
        await asyncio.sleep(e.retry_after)
        return await send_message_copy(message, chat_id)  # Recursive call

    except TelegramForbiddenError:
        logger.warning("[BROADCAST] Target [ID:%s]: bot was blocked", chat_id)
        return SendMessageStatus.BLOCKED

    except TelegramAPIError as exc:
        logger.exception("[BROADCAST] Target [ID:%s]: failed", chat_id, exc_info=exc)

    else:
        logger.info("[BROADCAST] Target [ID:%s]: success", chat_id)
        return SendMessageStatus.SUCCESS

    return SendMessageStatus.FAIL


def apply_active_date_filter(stmt: Select, min_date: datetime) -> Select:
    """
    Фильтрует активных за последнее время пользователей
    """
    # noinspection PyTypeChecker
    return (
        stmt.join(User, User.telegram_user_id == TelegramChat.id)
        .where(User.last_interaction >= min_date)
        .where(~User.banned)
    )


async def broadcast_message(message: Message, db_session: AsyncSession, logging_message: Message | None = None) -> int:
    """
    Рассылает копию сообщения всем активным пользователям из базы данных
    """

    last_interaction_min_date = datetime.now(UTC) - timedelta(seconds=ACTIVE_USER_TIMEOUT)

    # Считаем, сколько нужно разослать
    count_stmt = apply_active_date_filter(
        stmt=select(func.count()).select_from(TelegramChat),
        min_date=last_interaction_min_date,
    )
    count = cast(int, await db_session.scalar(count_stmt))

    if count == 0:
        logger.info("No users for broadcast")
        await message.reply("Некому делать рассылку")
        return 0

    await message.reply(
        f"Начинаю рассылку {count} {get_user_word(count)}, "
        f"{get_kotoriy_bil_activniy_word(count)} не более, "
        f"чем {seconds_to_human_readable(ACTIVE_USER_TIMEOUT)} назад",
    )

    chat_id_stmt = apply_active_date_filter(select(TelegramChat.id), last_interaction_min_date)
    return await broadcast(
        send_method=send_message_copy,
        chat_ids=(await db_session.scalars(chat_id_stmt)).yield_per(1000),
        count=count,
        logging_message=logging_message,
        message=message,
    )


async def broadcast_text(
    bot: Bot,
    text: str,
    chat_ids: Iterable[int],
    count: int,
    logging_message: Message | None = None,
) -> int:
    """
    Массовая рассылка текста

    Про параметры подробнее см функцию broadcast
    """
    return await broadcast(
        bot.send_message,
        chat_ids=chat_ids,
        count=count,
        logging_message=logging_message,
        text=text,
    )
