"""
Базовые классы для работы приложения администрирования
"""

import logging
import sys
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Any, ClassVar, TypeVar, cast

from sqlalchemy import ColumnElement, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import sqltypes
from sqlalchemy.sql._typing import _ColumnExpressionOrStrLabelArgument

from djgram.configs import ADMIN_ROWS_PER_PAGE
from djgram.db.models import BaseModel
from djgram.db.utils import get_fields_of_model

from .action_buttons import AbstractObjectActionButton
from .rendering import AdminFieldRenderer, AutoRenderer

T = TypeVar("T", bound="ModelAdmin")

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class ModelAdmin:
    """
    Модель админки, как в django (не относится к базе данных на прямую)
    """

    model: ClassVar[type[BaseModel]]  # Модель в которой есть id
    ordering: ClassVar[
        _ColumnExpressionOrStrLabelArgument[Any] | Sequence[_ColumnExpressionOrStrLabelArgument[Any]] | None
    ] = desc("id")
    name: ClassVar[str] = ""  # Название
    list_display: ClassVar[Sequence[str]] = []  # Список колонок для показа при предпросмотре
    search_fields: ClassVar[Sequence[str]] = []  # Список полей, по которым производиться поиск
    show_count: ClassVar[bool] = True  # Показывать число записей
    show_docs: ClassVar[bool] = True  # Показывать документацию, если есть

    # Список полей для показа, если None, то показываются все поля
    fields: ClassVar[Sequence[str | AdminFieldRenderer] | None] = None
    # Список полей для исключения. Учитывается, только если не определён fields
    exclude_fields: ClassVar[Sequence[str] | None] = None
    # Виджеты для конкретных полей
    widgets_override: ClassVar[dict[str, type[AdminFieldRenderer]]] = {}

    skip_synonyms_origin: ClassVar[bool] = True  # Не показывать поля, для которых есть синонимы

    # Кнопки действия с объектом в админке
    object_action_buttons: ClassVar[Sequence[AbstractObjectActionButton]] = []

    @classmethod
    def __check_fields_exists(cls, fields: Sequence[str], allowed_fields: set[str], list_name: str) -> None:
        extra_fields = set(fields) - allowed_fields

        errors = set()
        for extra_field in extra_fields:
            extra_field = extra_field.split(":", maxsplit=1)[-1]  # noqa: PLW2901

            # todo добавить валидацию таких полей - полей у внешних ключей
            if "__" not in extra_field and not hasattr(cls.model, extra_field):
                errors.add(extra_field)

        if len(errors) > 0:
            raise ValueError(f"У {cls} есть лишние поля в {list_name}: {sorted(errors)}")

    def __init_subclass__(cls, **kwargs):
        if cls.model is None:
            logger.critical("У %s не определена модель", cls)
            sys.exit()

        if len(cls.list_display) == 0:
            logger.critical("У %s не заполнен list_display", cls)
            sys.exit()

        if cls.name == "":
            logger.critical("У %s не заполнен name", cls)
            sys.exit()

        allowed_fields = set(get_fields_of_model(cls.model, skip_synonyms_origin=False))
        cls.__check_fields_exists(cls.list_display, allowed_fields, "list_display")
        cls.__check_fields_exists(cls.search_fields, allowed_fields, "search_fields")

    @classmethod
    async def display_name(cls, db_session: AsyncSession) -> str:
        if cls.show_count:
            count_stmt = select(func.count()).select_from(cls.model)
            count = await db_session.scalar(count_stmt)
            return f"{cls.name} ({count})"
        return cls.name

    @classmethod
    def get_fields(cls) -> Sequence[str | AdminFieldRenderer]:
        if cls.fields is not None:
            return cls.fields

        fields = get_fields_of_model(cls.model, cls.skip_synonyms_origin)

        if cls.exclude_fields is not None:
            exclude_fields = cast(Sequence[str], cls.exclude_fields)
            fields = list(filter(lambda f: f not in exclude_fields, fields))

        return fields

    @classmethod
    def get_fields_widgets(cls) -> list[AdminFieldRenderer]:
        widgets: list[AdminFieldRenderer] = []

        for field in cls.get_fields():
            if isinstance(field, str):
                widget = cls.widgets_override.get(field, AutoRenderer)(field)
            else:
                new_class = cls.widgets_override.get(field.field)
                widget = new_class(field.field) if new_class is not None else field

            widgets.append(widget)

        return widgets

    @classmethod
    def generate_search_filter(cls, query: str) -> ColumnElement[bool]:
        ors = []

        allowed_fields = set(get_fields_of_model(cls.model, skip_synonyms_origin=True))
        ilike_query = None
        for field_name in set(cls.search_fields) & allowed_fields:  # todo: добавить фильтрацию по внешним ключам
            field = getattr(cls.model, field_name)
            # Все возможные Varchar, Char, Text - подклассы String
            if isinstance(field.type, sqltypes.String):
                if ilike_query is None:
                    ilike_query = f"%{query}%"
                ors.append(field.ilike(ilike_query))
            elif isinstance(field.type, sqltypes.Integer):
                with suppress(ValueError):
                    ors.append(field == int(query))
            elif isinstance(field.type, sqltypes.Float):
                with suppress(ValueError):
                    ors.append(field == float(query))
            else:
                ors.append(field == query)

        return or_(*ors)

    @classmethod
    def get_object_action_button_by_id(cls, button_id: str) -> AbstractObjectActionButton | None:
        # Тут можно сделать поиск по словарю, если сделать его через метакласс
        # Но это не имеет смысла, так как всего кнопок не очень большое количество
        for btn in cls.object_action_buttons:
            if btn.button_id == button_id:
                return btn

        return None


@dataclass
class AppAdmin:
    """
    Модель администрирования для приложения

    Attributes:
        verbose_name(str): Человекочитаемое название приложение
        admin_models(list[ModelAdmin]): Список всех административных панелей в приложении
    """

    verbose_name: str

    admin_models: list[type[ModelAdmin]] = dc_field(default_factory=list)

    rows_per_page: int = ADMIN_ROWS_PER_PAGE

    def __post_init__(self) -> None:
        """
        Регистрирует админку для приложения
        """
        apps_admins.append(self)
        logger.info('Registered "%s" admin', self.verbose_name)

    def register(self, admin_model: type[T]) -> type[T]:
        self.admin_models.append(admin_model)
        return admin_model


apps_admins: list[AppAdmin] = []
