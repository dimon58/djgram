"""
Посредники для аналитики
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

import orjson
from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.middlewares.user_context import EVENT_CONTEXT_KEY, EventContext, UserContextMiddleware
from aiogram.types import Update

from djgram.configs import ANALYTICS_UPDATES_TABLE
from djgram.contrib.analytics.misc import UPDATE_DDL_SQL
from djgram.db import clickhouse

CONTENT_TYPE_KEY = "content_type"
logger = logging.getLogger(__name__)

try:
    # noinspection PyUnresolvedReferences
    from aiogram.client.default import Default

    def set_defaults(data: dict, bot: Bot) -> dict:
        """
        Устанавливает все значения defaults в данных
        """

        for key, value in data.items():
            if isinstance(value, Default):
                data[key] = bot.default[value.name]

            elif isinstance(value, dict):
                data[key] = set_defaults(value, bot)

        return data

except ImportError:

    def set_defaults(data: dict, bot: Bot) -> dict:
        return data


def get_update_dict_for_clickhouse(
    update: Update,
    execution_time: float,
    event_context: EventContext,
    bot: Bot,
) -> dict[str, Any]:
    update.message.from_user.is_premium = None
    event = update.model_dump(mode="python", exclude_unset=True)
    event = set_defaults(event, bot)

    return {
        "date": datetime.now(tz=UTC),
        "execution_time": execution_time,
        "event_type": update.event_type,  # property
        CONTENT_TYPE_KEY: getattr(update.event, CONTENT_TYPE_KEY, None),
        "user_id": event_context.user_id,
        "chat_id": event_context.chat_id,
        "thread_id": event_context.thread_id,
        "business_connection_id": event_context.business_connection_id,
        "update_id": event.pop("update_id"),
        "event": orjson.dumps(event),
    }


# pylint: disable=too-few-public-methods
async def save_event_to_clickhouse(
    update: Update,
    execution_time: float,
    event_context: EventContext,
    bot: Bot,
) -> int | None:
    """
    Сохраняет update в clickhouse
    """

    data = get_update_dict_for_clickhouse(
        update=update,
        execution_time=execution_time,
        event_context=event_context,
        bot=bot,
    )

    try:
        async with clickhouse.connection() as clickhouse_connection:
            return await clickhouse.insert_dict(clickhouse_connection, ANALYTICS_UPDATES_TABLE, data)

    # pylint: disable=broad-exception-caught
    except Exception as exc:
        logger.exception(
            "Inserting in clickhouse error: %s: %s", exc.__class__.__name__, exc, exc_info=exc  # noqa: TRY401
        )
        return None


class SaveUpdateToClickHouseMiddleware(BaseMiddleware):
    """
    Сохраняет все update'ы в ClickHouse
    """

    def __init__(self):  # noqa: D107
        logger.debug("Ensuring clickhouse tables for updates")
        with open(UPDATE_DDL_SQL, encoding="utf-8") as sql_file:  # noqa: PTH123
            clickhouse.run_sql_from_sync(sql_file.read())

        # Задачи сохранения аналитики в clickhouse
        # Временно сохраняем из тут, чтобы сборщик мусора не убил раньше времени
        # https://docs.python.org/3.12/library/asyncio-task.html#asyncio.create_task
        self.pending_tasks = set[asyncio.Task]()

    async def __call__(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:
        start = perf_counter()
        result = await handler(update, data)
        finish = perf_counter()

        # Если перед этой мидлварью установлена UserContextMiddleware из aiogram, то есть event_context
        event_context: EventContext = data.get(EVENT_CONTEXT_KEY)
        if event_context is not None:
            event_context = UserContextMiddleware.resolve_event_context(update)

        task = asyncio.create_task(
            save_event_to_clickhouse(
                update=update,
                execution_time=finish - start,
                event_context=event_context,
                bot=data["bot"],
            )
        )
        task.add_done_callback(self.pending_tasks.remove)
        # Храним ссылку на задачу, чтобы она не уничтожилась в процессе выполнения
        self.pending_tasks.add(task)

        return result
