"""
Классы для рендеринга полей
"""

import html
import json
import logging
from abc import abstractmethod
from datetime import date, datetime
from enum import Enum
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, ClassVar, cast
from uuid import UUID

import pydantic
from djgram.db.models import BaseModel
from djgram.utils.formating import get_bytes_size_format
from sqlalchemy_file import File

if TYPE_CHECKING:
    from sqlalchemy import Column
    from sqlalchemy_utils import PhoneNumber

QUERY_KEY = "query"

logger = logging.getLogger(__name__)


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


def get_field_by_path(obj: BaseModel, field: str) -> Any:  # noqa: C901, PLR0912
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
    """
    Базовый класс рендерера виджета в админке
    """

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

    def render_head(self, obj: BaseModel, *, render_docs: bool) -> list[str]:
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

    def render_for_obj(self, obj: BaseModel, *, render_docs: bool) -> str:
        """
        Рендерит объект поля в виде

        **Заголовок**
        **Тело**

        Args:
            obj: объект для которого рендериться представление
            render_docs: нудно ли рендерить документацию. Не рендериться, если поле составное
        Returns:
            str: строка с отрендеренным значением
        """
        head = self.render_head(obj, render_docs=render_docs)
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

    def get_data(self, obj: BaseModel) -> str | None:
        return f"<code>{html_escape(self.get_from_obj(obj))}</code>"

    def render_for_obj(self, obj: BaseModel, *, render_docs: bool) -> str:
        head = [f"<strong>●{self.get_title()}:</strong> {self.get_data(obj)}"]

        if render_docs:
            doc = self.render_docs(obj)

            if doc is not None:
                head.append(doc)

        return "\n".join(head)


class SpecialStringOneLineTextRenderer(OneLineTextRenderer):  # noqa: D101
    @abstractmethod
    def prepare_data(self, obj: BaseModel) -> str | None:
        raise NotImplementedError

    def get_data(self, obj: BaseModel) -> str | None:
        return html_escape(self.prepare_data(obj))


class TelegramUsernameLinkRenderer(SpecialStringOneLineTextRenderer):
    """
    Рендерит кликабельно имя пользователя в тг
    """

    def prepare_data(self, obj: BaseModel) -> str | None:
        username: str | None = self.get_from_obj(obj)

        return f"@{username}" if username is not None else "-"


class PhoneNumberRenderer(SpecialStringOneLineTextRenderer):
    """
    Рендерит кликабельный номер телефона в тг
    """

    def prepare_data(self, obj: BaseModel) -> str:
        phone_number: PhoneNumber | None = self.get_from_obj(obj)
        if phone_number is not None:
            return phone_number.e164

        return "-"


class HttpStatusRenderer(SpecialStringOneLineTextRenderer):
    """
    Ренедерит статус код http
    """

    @classmethod
    def get_code_phrase(cls, code: int) -> str:
        # noinspection PyProtectedMember
        status = cast(HTTPStatus | None, HTTPStatus._value2member_map_.get(code, None))
        return status.phrase if status is not None else "Unknown"

    def prepare_data(self, obj: BaseModel) -> str:
        http_status_code: int | None = self.get_from_obj(obj)
        if http_status_code is None:
            return "-"

        phrase = self.get_code_phrase(http_status_code)
        return f"<code>{html_escape(http_status_code)} {html_escape(phrase)}</code>"

    def get_data(self, obj: BaseModel) -> str | None:
        return self.prepare_data(obj)


class WebsocketStatusRenderer(HttpStatusRenderer):
    """
    Ренедерит статус код http
    """

    WEBSOCKET_STATUS_CODES: ClassVar[dict[int, str]] = {
        1000: "Normal Closure",
        1001: "Going Away",
        1002: "Protocol Error",
        1003: "Unsupported Data",
        1005: "No Status Received",
        1006: "Abnormal Closure",
        1007: "Invalid Frame Payload Data",
        1008: "Policy Violation",
        1009: "Message Too Big",
        1010: "Mandatory Extension",
        1011: "Internal Server Error",
        1012: "Service Restart",
        1013: "Try Again Later",
        1014: "Bad gateway",
        1015: "TLS Handshake",
    }

    @classmethod
    def get_code_phrase(cls, code: int) -> str:
        return cls.WEBSOCKET_STATUS_CODES.get(code, "Unknown")


class EmailRenderer(SpecialStringOneLineTextRenderer):
    """
    Рендерит кликабельную электронную почту в тг
    """

    def prepare_data(self, obj: BaseModel) -> str:
        email: str | None = self.get_from_obj(obj)

        return email if email is not None else "-"


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

    indent = 2

    def json_dumps_support_pydantic(self, obj: Any) -> str:
        if isinstance(obj, pydantic.BaseModel):
            return obj.model_dump_json(indent=self.indent)

        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    def render_body(self, obj: BaseModel) -> str:
        data = self.get_from_obj(obj)
        if data is None:
            return "<pre>None</pre>"
        data = json.dumps(data, ensure_ascii=False, indent=self.indent, default=self.json_dumps_support_pydantic)
        return f'<pre><code class="json">{html_escape(data)}</code></pre>'


class PydanticRenderer(JsonRenderer):
    """
    Отображает модели pydantic в виде json

    Можно использовать, если тип колонки это PydanticField или ImmutablePydanticField
    """

    def render_body(self, obj: BaseModel) -> str:
        data = self.get_from_obj(obj)
        if data is None:
            return "<pre>None</pre>"
        data = data.model_dump_json(indent=2)
        return f'<pre><code class="json">{html_escape(data)}</code></pre>'


class FileRenderer(AdminFieldRenderer):
    """
    Отображает файл в виде filename (size)

    Например: document.pdf (1.23 MB)
    """

    def render_for_obj(self, obj: BaseModel, *, render_docs: bool) -> str:
        data = self.get_from_obj(obj)

        head = [
            f"<strong>●{self.get_title()}:</strong> "
            f"<code>{html_escape(data['filename'])}</code> ({get_bytes_size_format(data['size'])})",
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

    def render_for_obj(self, obj: BaseModel, *, render_docs: bool) -> str:
        data = self.get_from_obj(obj)

        # Тут функция get_from_obj будет вызываться 2 раза
        if isinstance(data, None | bool | int | float | date | datetime | UUID) or (
            isinstance(data, str) and len(data) == 0
        ):
            renderer = OneLineTextRenderer(self._field, self._title, self._docs)

        elif isinstance(data, File):
            renderer = FileRenderer(self._field, self._title, self._docs)

        elif isinstance(data, dict | list):
            renderer = JsonRenderer(self._field, self._title, self._docs)

        elif isinstance(data, pydantic.BaseModel):
            renderer = PydanticRenderer(self._field, self._title, self._docs)

        else:
            renderer = super()

        return renderer.render_for_obj(obj, render_docs=render_docs)
