from collections.abc import AsyncGenerator, Iterable
from contextlib import asynccontextmanager
from typing import Any

import orjson
from asynch import connect
from asynch.connection import Connection

from djgram import configs


def monkey_patch_asynch() -> None:
    """
    Фикс сериализации json для datetime внутри словарей и не только
    """
    from asynch.proto.columns.jsoncolumn import JsonColumn

    async def write_items(self: JsonColumn, items: list[Any]) -> None:
        items = [x if isinstance(x, str) else orjson.dumps(x) for x in items]
        await self.string_column.write_items(items)

    JsonColumn.write_items = write_items


monkey_patch_asynch()


# todo: по хорошему надо сделать пул соединений
async def get_connection() -> Connection:
    return await connect(
        host=configs.CLICKHOUSE_HOST,
        port=configs.CLICKHOUSE_PORT,
        database=configs.CLICKHOUSE_DB,
        user=configs.CLICKHOUSE_USER,
        password=configs.CLICKHOUSE_PASSWORD,
    )


@asynccontextmanager
async def connection() -> AsyncGenerator[Connection, None, None]:
    """
    Обертка над get_connection в виде контекстного менеджера
    """
    yield await get_connection()


def get_insert_sql(table_name: str, columns: Iterable[str]) -> str:
    """
    Создаёт sql для вставки в clickhouse

    Args:
        table_name: название таблицы
        columns: название колонок для вставки

    Returns:
        Запрос для вставки в clickhouse
    """
    keys_str = ",".join(columns)
    return f"INSERT INTO {table_name}({keys_str}) VALUES"


async def insert_dict(client: Connection, table_name: str, data: dict[str, Any]) -> int:
    """
    Вставляет словарь в clickhouse

    Args:
        client: клиент clickhouse
        table_name: название таблицы
        data: словарь с данными для вставки

    Returns:
        Число вставленных строк
    """

    sql = get_insert_sql(table_name, data.keys())
    values = (tuple(data.values()),)
    async with client.cursor() as cursor:
        return await cursor.execute(sql, values)
