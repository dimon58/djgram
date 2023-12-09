"""
Посредники для аналитики
"""
import logging
from abc import ABC
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Update

from djgram.configs import ANALYTICS_UPDATES_TABLE
from djgram.db import clickhouse

logger = logging.getLogger(__name__)


def get_update_dict_for_clickhouse(update: Update, execution_time: float):
    data = update.model_dump()
    data["date"] = datetime.now(tz=UTC)
    data["execution_time"] = execution_time
    data["event_type"] = update.event_type  # property
    if update.event_type == "message":
        # noinspection PyUnresolvedReferences
        data["content_type"] = update.event.content_type

    # Убираем лишние поля, которые могут появиться во время обработки update'а
    possible_fields = {"date", "execution_time", "event_type", "content_type"} | set(Update.model_fields.keys())
    for key in data:
        if key not in possible_fields:
            data.pop(key)

    return data


# pylint: disable=too-few-public-methods
async def save_event_to_clickhouse(update: Update, execution_time: float):
    """
    Сохраняет update в clickhouse
    """
    data = get_update_dict_for_clickhouse(update, execution_time)

    try:
        with clickhouse.connection() as clickhouse_connection:
            # если не установлен orjson, то будет ругаться на невозможность сериализовать datetime внутри message
            clickhouse.insert_dict(clickhouse_connection, ANALYTICS_UPDATES_TABLE, data)
    # pylint: disable=broad-exception-caught
    except Exception as exc:
        logger.exception(f"Inserting in clickhouse error: {exc.__class__.__name__}: {exc}")


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
        await save_event_to_clickhouse(update, finish - start)

        return result
