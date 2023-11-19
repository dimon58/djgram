from contextlib import contextmanager
from typing import Any, Iterable

from clickhouse_driver import Client

import configs


# todo: по хорошему надо сделать пул соединений
def get_connection() -> Client:
    return Client(
        host=configs.CLICKHOUSE_HOST,
        port=configs.CLICKHOUSE_PORT,
        database=configs.CLICKHOUSE_DB,
        user=configs.CLICKHOUSE_USER,
        password=configs.CLICKHOUSE_PASSWORD,
    )


@contextmanager
def connection():
    """
    Обертка над get_connection в виде контекстного менеджера
    """
    yield get_connection()


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


def insert_dict(client: Client, table_name: str, data: dict[str, Any]) -> int:
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
    return client.execute(sql, values)
