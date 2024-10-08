import asyncio
import logging
import os
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, TypeAlias, TypeVar

import orjson
from aiogram import Bot
from aiogram.methods import TelegramMethod
from aiogram.types import BufferedInputFile, FSInputFile, InputFile, URLInputFile

from djgram.configs import ANALYTICS_BOT_SEND_TABLE
from djgram.contrib.logs.context import UPDATE_ID
from djgram.db import clickhouse
from djgram.utils.input_file_ext import S3FileInput
from djgram.utils.serialization import jsonify
from djgram.utils.upload import LoggingInputFile

from .misc import BOT_SEND_ANALYTICS_DDL_SQL
from .utils import set_defaults

T = TypeVar("T")

BotCallMethod: TypeAlias = Callable[[Bot, TelegramMethod[T], int | None], Awaitable[T]]

logger = logging.getLogger(__name__)

_pending_tasks = set[asyncio.Task]()


def _serialize_input_file(input_file: InputFile) -> dict[str, Any]:

    if isinstance(input_file, LoggingInputFile):
        input_file = input_file.real_input_file

    data = {
        "type": input_file.__class__.__name__,
        "file_name": input_file.filename,
        "chunk_size": input_file.chunk_size,
    }

    if isinstance(input_file, BufferedInputFile):
        data["file_size"] = len(input_file.data)

    elif isinstance(input_file, FSInputFile):
        data["file_size"] = os.path.getsize(input_file.path)  # noqa: PTH202

    elif isinstance(input_file, URLInputFile):
        data["url"] = input_file.url
        data["headers"] = input_file.headers
        data["timeout"] = input_file.timeout

    elif isinstance(input_file, S3FileInput):
        data["file_size"] = input_file.obj.size
        data["name"] = input_file.obj.name
        data["hash"] = input_file.obj.hash
        data["container"] = input_file.obj.container.name
        data["extra"] = input_file.obj.extra
        data["meta_data"] = input_file.obj.meta_data
        data["driver"] = input_file.obj.driver.name

    return data


def _serialize_default(obj: Any) -> Any:
    if isinstance(obj, InputFile):
        return _serialize_input_file(obj)

    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def analytics_wrapper(original_call: BotCallMethod) -> BotCallMethod:
    """
    Логирует все вызываемые методы bot api в clickhouse
    """

    async def __call__(self: Bot, method: TelegramMethod[T], request_timeout: int | None = None) -> T:  # noqa: N807
        date = datetime.now(tz=UTC)

        start = time.perf_counter()
        answer = await original_call(self, method, request_timeout)
        end = time.perf_counter()

        method_data = method.model_dump(mode="python", exclude_unset=True)
        method_data = set_defaults(method_data, self)

        data = {
            "update_id": UPDATE_ID.get(),
            "bot_id": self.id,
            "date": date,
            "method": method.__class__.__name__,
            "method_data": orjson.dumps(method_data, default=_serialize_default),
            "execution_time": end - start,
            "request_timeout": request_timeout,
            "answer": orjson.dumps(jsonify(answer)),
        }

        task = asyncio.create_task(clickhouse.safe_insert_dict(ANALYTICS_BOT_SEND_TABLE, data))
        task.add_done_callback(_pending_tasks.remove)
        _pending_tasks.add(task)

        return answer

    return __call__


def setup_bot_answer_analytics():
    logger.debug("Ensuring clickhouse tables for bot send analytics")
    with open(BOT_SEND_ANALYTICS_DDL_SQL, encoding="utf-8") as sql_file:  # noqa: PTH123
        task = clickhouse.run_sql_from_sync(sql_file.read())
        task.add_done_callback(_pending_tasks.remove)
        _pending_tasks.add(task)

    Bot.__call__ = analytics_wrapper(Bot.__call__)
