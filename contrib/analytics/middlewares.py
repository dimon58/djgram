"""
Посредники для аналитики
"""

import asyncio
import copy
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, Generic, TypeVar, cast

import orjson
from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.middlewares.user_context import EVENT_CONTEXT_KEY, EventContext, UserContextMiddleware
from aiogram.types import CallbackQuery, Message, Update
from aiogram_dialog import DialogProtocol
from aiogram_dialog.api.entities import Context, Stack
from aiogram_dialog.api.internal import CONTEXT_KEY, STACK_KEY
from djgram.configs import ANALYTICS_UPDATES_TABLE
from djgram.db import clickhouse

from .dialog_analytics import save_input_statistics, save_keyboard_statistics
from .misc import UPDATE_DDL_SQL
from .utils import set_defaults

T = TypeVar("T")
V = TypeVar("V")
CONTENT_TYPE_KEY = "content_type"
logger = logging.getLogger(__name__)


def get_update_dict_for_clickhouse(
    update: Update,
    execution_time: float,
    event_context: EventContext,
    bot: Bot,
) -> dict[str, Any]:
    event = update.model_dump(mode="python", exclude_unset=True)
    event = set_defaults(event, bot)

    return {
        "date": datetime.now(tz=UTC),
        "execution_time": execution_time,
        "event_type": update.event_type,  # property
        CONTENT_TYPE_KEY: getattr(update.event, CONTENT_TYPE_KEY, None),
        "bot_id": bot.id,
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

    return await clickhouse.safe_insert_dict(ANALYTICS_UPDATES_TABLE, data)


class SaveUpdateToClickHouseMiddleware(BaseMiddleware):
    """
    Сохраняет все update'ы в ClickHouse
    """

    def __init__(self):  # noqa: D107
        # Задачи сохранения аналитики в clickhouse
        # Временно сохраняем из тут, чтобы сборщик мусора не убил раньше времени
        # https://docs.python.org/3.12/library/asyncio-task.html#asyncio.create_task
        self.pending_tasks = set[asyncio.Task]()

        logger.debug("Ensuring clickhouse tables for updates")
        with open(UPDATE_DDL_SQL, encoding="utf-8") as sql_file:  # noqa: PTH123
            task = clickhouse.run_sql_from_sync(sql_file.read())
            task.add_done_callback(self.pending_tasks.remove)
            self.pending_tasks.add(task)

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
        event_context: EventContext | None = data.get(EVENT_CONTEXT_KEY)
        if event_context is not None:
            event_context = UserContextMiddleware.resolve_event_context(update)

        task = asyncio.create_task(
            save_event_to_clickhouse(
                update=update,
                execution_time=finish - start,
                event_context=cast(EventContext, event_context),
                bot=data["bot"],
            ),
        )
        task.add_done_callback(self.pending_tasks.remove)
        # Храним ссылку на задачу, чтобы она не уничтожилась в процессе выполнения
        self.pending_tasks.add(task)

        return result


class DialogAnalyticsInnerMiddleware(BaseMiddleware, Generic[T]):
    """
    Сохраняет действия пользователя в диалоге
    """

    @classmethod
    async def save_statistics(  # noqa: PLR0913
        cls,
        process_time: float,
        event: T,
        middleware_data: dict[str, Any],
        state_before: str | None,
        aiogd_stack_before: Stack | None,
        aiogd_context_before: Context | None,
    ) -> None:
        raise NotImplementedError

    async def __call__(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        handler: Callable[[T, dict[str, Any]], Awaitable[V]],
        event: T,
        data: dict[str, Any],
    ) -> V:
        # Находились в диалоге -> событие сохраниться с помощью
        # contrib.analytics.dialog_analytics.keyboard_process_callback
        event_handler = data["handler"].callback
        if hasattr(event_handler, "__self__") and isinstance(event_handler.__self__, DialogProtocol):
            return await handler(event, data)

        aiogd_stack_before: Stack | None = copy.deepcopy(data.get(STACK_KEY))
        aiogd_context_before: Context | None = copy.deepcopy(data.get(CONTEXT_KEY))
        state_before: str | None = await data["state"].get_state()

        start = time.perf_counter()
        result = await handler(event, data)
        end = time.perf_counter()

        await self.save_statistics(
            process_time=end - start,
            event=event,
            middleware_data=data,
            state_before=state_before,
            aiogd_stack_before=aiogd_stack_before,
            aiogd_context_before=aiogd_context_before,
        )

        return result


class DialogAnalyticsInnerMessageMiddleware(DialogAnalyticsInnerMiddleware[Message]):  # noqa: D101
    @classmethod
    async def save_statistics(  # noqa: PLR0913
        cls,
        process_time: float,
        event: Message,
        middleware_data: dict[str, Any],
        state_before: str | None,
        aiogd_stack_before: Stack | None,
        aiogd_context_before: Context | None,
    ) -> None:
        await save_input_statistics(
            processor=cls.__name__,
            processed=True,
            process_time=process_time,
            not_processed_reason=None,
            input_=None,
            message=event,
            middleware_data=middleware_data,
            state_before=state_before,
            aiogd_context_before=aiogd_context_before,
            aiogd_stack_before=aiogd_stack_before,
        )


class DialogAnalyticsInnerCallbackQueryMiddleware(DialogAnalyticsInnerMiddleware[CallbackQuery]):  # noqa: D101
    @classmethod
    async def save_statistics(  # noqa: PLR0913
        cls,
        process_time: float,
        event: CallbackQuery,
        middleware_data: dict[str, Any],
        state_before: str | None,
        aiogd_stack_before: Stack | None,
        aiogd_context_before: Context | None,
    ) -> None:
        await save_keyboard_statistics(
            processor=cls.__name__,
            processed=True,
            process_time=process_time,
            keyboard=None,
            callback=event,
            middleware_data=middleware_data,
            state_before=state_before,
            aiogd_context_before=aiogd_context_before,
            aiogd_stack_before=aiogd_stack_before,
        )
