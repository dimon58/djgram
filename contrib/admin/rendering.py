"""
Классы для рендеринга полей
"""

import html
import json
import logging
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy_file import File

from djgram.db.models import BaseModel
from djgram.utils.formating import get_bytes_size_format

if TYPE_CHECKING:
    from sqlalchemy import Column
logger = logging.getLogger(__name__)
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


def get_field_by_path(obj: BaseModel, field: str) -> Any:
    """
    Возвращает значения поля объекта по пути

    Работает с вложенными полями в json
    """
    _value = obj
    _prev_chain = None
    for chain in field.split("__"):
        _prev_value = _value

        if isinstance(_value, dict):  # если это json
            if chain not in _value:
                logger.warning("There is no %s in json from column %s from %s", chain, field, obj.__class__)
                _value = None
            else:
                _value = _value.get(chain)
        elif isinstance(_value, list):
            if chain.isnumeric():
                int_chain = int(chain)
                if len(_value) > int_chain:
                    _value = _value[int_chain]
                else:
                    logger.warning(
                        "List length = %s < %s in column %s at %s from %s",
                        len(_value),
                        int_chain + 1,
                        field,
                        _prev_chain,
                        obj.__class__,
                    )
                    _value = None
            else:
                logging.warning(
                    "Index of list %s from column %s from %s should be integer, not %s",
                    _prev_chain,
                    field,
                    obj.__class__,
                    chain,
                )
                _value = None
        elif _value is None:
            logging.warning("None value in %s from column %s from %s", chain, field, obj.__class__)
        else:
            _value = getattr(_value, chain)

        # Если встретилось свойство, то достаём его значение
        if isinstance(_value, property):
            _value = property.__get__(_value, _prev_value)

        _prev_chain = chain

    # Превращаем Enum в его значение
    if isinstance(_value, Enum):
        _value = _value.value

    return _value


class AdminFieldRenderer:
    def __init__(self, field: str, title: str | None = None, docs: str | None = None):
        """
        Args:
            field: Путь до поля, в том числе составной, разделённый __, как в django.
                Например name, json_data__field_name, json_data__some_list__0.
            title: Новое название поля
            docs: Новая документация для поля
        """
        self._field = field
        self._title = title
        self._docs = docs

    def __str__(self):
        return f"{self.__class__.__name__}({self._field})"

    @property
    def field(self) -> str:
        return self._field

    def get_from_obj(self, obj: BaseModel) -> Any:
        """
        Возвращает значения поля объекта по пути

        Работает с вложенными полями в json
        """
        return get_field_by_path(obj, self._field)

    def render_docs(self, obj: BaseModel) -> str | None:
        """
        Рендерит документацию в виде

        <i>Документация</i>
        """
        if self._docs is not None:
            doc = self._docs
        elif "__" not in self._field:
            column: Column = getattr(obj.__class__, self._field)
            doc = getattr(column, "doc", None)  # У Relationship нет документации
        else:
            doc = None

        if doc is None:
            return None

        return f"<i>{html_escape(doc)}</i>"

    def get_title(self) -> str:
        """
        Возвращает названия поля с учётом возможного переопределения
        """
        return self._title if self._title is not None else self._field

    def render_head(self, obj: BaseModel, render_docs: bool) -> list[str]:
        """
        Рендерит заголовок в виде

        <strong>Название</strong>
        <i>Документация</i> - Если нужно рендерить документацию

        Args:
            obj: объект для которого рендериться представление
            render_docs: нудно ли рендерить документацию. Не рендериться, если поле составное
        Returns:
            str: список строк заголовка
        """

        head = [f"<strong>●{self.get_title()}</strong>"]

        if not render_docs:
            return head

        doc = self.render_docs(obj)

        if doc is not None:
            head.append(doc)

        return head

    def render_body(self, obj: BaseModel) -> str:
        """
        Рендерит тело поля, Например <pre>Значение</pre>

        Args:
            obj: объект для которого рендериться представление
        Returns:
            str: строка с отрендереным значением
        """
        raise NotImplementedError

    def render_for_obj(self, obj: BaseModel, render_docs: bool) -> str:
        """
        Рендерит объект поля в виде

        **Заголовок**
        **Тело**

        Args:
            obj: объект для которого рендериться представление
            render_docs: нудно ли рендерить документацию. Не рендериться, если поле составное
        Returns:
            str: строка с отрендереным значением
        """
        head = self.render_head(obj, render_docs)
        head.append(self.render_body(obj))

        return "\n".join(head)


class TextRenderer(AdminFieldRenderer):
    """
    Рендерит, как моноширинный текст
    """

    def render_body(self, obj: BaseModel) -> str:
        return f"<pre>{html_escape(self.get_from_obj(obj))}</pre>"


class OneLineTextRenderer(AdminFieldRenderer):
    """
    Рендерит в виде

    ●Название: значение
    Документация
    """

    def render_for_obj(self, obj: BaseModel, render_docs: bool) -> str:
        head = [f"<strong>●{self.get_title()}:</strong> <code>{html_escape(self.get_from_obj(obj))}</code>"]

        if render_docs:
            doc = self.render_docs(obj)

            if doc is not None:
                head.append(doc)

        return "\n".join(head)


class TelegramUsernameLinkRenderer(OneLineTextRenderer):
    """
    Рендерит кликабельно имя пользователя в тг
    """

    def render_for_obj(self, obj: BaseModel, render_docs: bool) -> str:
        username = html_escape(self.get_from_obj(obj))

        username = f"@{username}" if username is not None else "-"

        head = [f"<strong>●{self.get_title()}:</strong> {username}"]

        if render_docs:
            doc = self.render_docs(obj)

            if doc is not None:
                head.append(doc)

        return "\n".join(head)


class JsonRenderer(AdminFieldRenderer):
    """
    Ренедерит в виде форматированного json. Например:


    ●Название
    Документация
    ```json
    {
        "a": 1,
        "b": {
            "c": 2
        }
    }
    ```
    """

    def render_body(self, obj: BaseModel) -> str:
        data = self.get_from_obj(obj)
        if data is None:
            return "<pre>None</pre>"
        data = json.dumps(data, ensure_ascii=False, indent=2)
        return f'<pre><code class="json">{html_escape(data)}</code></pre>'


class FileRenderer(AdminFieldRenderer):
    """
    Отображает файл в виде filename (size)

    Например: document.pdf (1.23 MB)
    """

    def render_for_obj(self, obj: BaseModel, render_docs: bool) -> str:
        data = self.get_from_obj(obj)

        head = [
            f"<strong>●{self.get_title()}:</strong> "
            f"<code>{html_escape(data['filename'])}</code> ({get_bytes_size_format(data['size'])})"
        ]

        if render_docs:
            doc = self.render_docs(obj)

            if doc is not None:
                head.append(doc)

        return "\n".join(head)


class AutoRenderer(TextRenderer):
    """
    Автоматически выбирает способ отображения для данных
    """

    def render_for_obj(self, obj: BaseModel, render_docs: bool) -> str:

        data = self.get_from_obj(obj)

        # Тут функция get_from_obj будет вызываться 2 раза
        if isinstance(data, None | bool | int | float | date | datetime) or (isinstance(data, str) and len(data) == 0):
            renderer = OneLineTextRenderer(self._field, self._title, self._docs)

        elif isinstance(data, File):
            renderer = FileRenderer(self._field, self._title, self._docs)

        elif isinstance(data, dict | list):
            renderer = JsonRenderer(self._field, self._title, self._docs)

        else:
            renderer = super()

        return renderer.render_for_obj(obj, render_docs)
