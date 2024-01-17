"""
Утилиты для работы администрирования
"""
import html
from typing import Any

QUERY_KEY = "query"


def html_escape(obj: Any) -> str:
    return html.escape(str(obj))


def prepare_rows(rows: list[list[Any]]) -> list[str]:
    """
    Преобразует результат выполнения запроса к базе данных в список строк вида

    │значение_1│значение_2│...│значение_n│
    │значение_1│значе_2   │...│значение_n│
    │знач_1    │значение_2│...│значение_n│
    │значение_1│знач    _2│...│знач_n    │
    │знач    _1│знач    _2│...│знач_n    │

    То есть дополняет каждую строку пробелами до одинаковой длинны
    """

    # Если передан пустой список, то возвращаем пустой список
    if len(rows) == 0:
        return []

    if len(rows[0]) == 1:
        return [row[0] for row in rows]

    # Список с максимальными длинами каждого элемента, пока его просто инициализируем нулями
    max_lengths = [0 for _ in range(len(rows[0]))]

    # Ищем максимальную длину каждого элемента в строке
    for row in rows:
        for idx, (elem, max_len) in enumerate(zip(row, max_lengths, strict=True)):
            max_lengths[idx] = max(len(str(elem)), max_len)

    # Преобразуем данные в массив строк, каждая строка содержит элементы,
    # разделённые символом "│" и дополненные справа пробелами до соответствующей максимальной длины
    row_stings = []
    for row in rows:
        _row_string = "│"
        for elem, max_len in zip(row, max_lengths, strict=True):
            _row_string += f"{elem}{' ' * (((max_len - len(str(elem))) * 285) // 100)}│"

        row_stings.append(_row_string)

    return row_stings
