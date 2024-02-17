"""
Посредники для аналитики
"""

import logging
from abc import ABC
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.types import Update

from djgram.configs import ANALYTICS_UPDATES_TABLE
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


def get_update_dict_for_clickhouse(update: Update, execution_time: float, bot: Bot) -> dict[str, Any]:
    data = update.model_dump(mode="python")
    data = set_defaults(data, bot)
    data["date"] = datetime.now(tz=UTC)
    data["execution_time"] = execution_time
    data["event_type"] = update.event_type  # property
    data[CONTENT_TYPE_KEY] = getattr(update.event, CONTENT_TYPE_KEY, None)

    # Убираем лишние поля, которые могут появиться во время обработки update'а
    possible_fields = {"date", "execution_time", "event_type", "content_type"} | set(Update.model_fields.keys())
    for key in data:
        if key not in possible_fields:
            data.pop(key)

    return data


# pylint: disable=too-few-public-methods
async def save_event_to_clickhouse(update: Update, execution_time: float, bot: Bot) -> int | None:
    """
    Сохраняет update в clickhouse
    """
    data = get_update_dict_for_clickhouse(update, execution_time, bot)

    try:
        async with clickhouse.connection() as clickhouse_connection:
            return await clickhouse.insert_dict(clickhouse_connection, ANALYTICS_UPDATES_TABLE, data)

    # pylint: disable=broad-exception-caught
    except Exception as exc:
        logger.exception(
            "Inserting in clickhouse error: %s: %s", exc.__class__.__name__, exc, exc_info=exc  # noqa: TRY401
        )
        return None


class SaveUpdateToClickHouseMiddleware(BaseMiddleware, ABC):
    """
    Сохраняет все update'ы в ClickHouse
    """

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:
        start = perf_counter()
        result = await handler(update, data)
        finish = perf_counter()
        await save_event_to_clickhouse(update, finish - start, data["bot"])

        return result
