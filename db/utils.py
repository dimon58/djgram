"""
Утилиты для работы с базой данных
"""

import logging
from enum import Enum
from typing import Any, TypeVar, cast

from sqlalchemy import inspect, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import MappedColumn, RelationshipProperty, Synonym

from djgram.db.models import BaseModel

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class ReturnState(Enum):
    """
    Состояния возврата функции :func:insert_or_update:

    Attributes:
        NOT_MODIFIED: не изменён
        CREATED: создан
        UPDATED: обновлен
    """

    NOT_MODIFIED = 0
    CREATED = 1
    UPDATED = 2

    def need_commit(self) -> bool:
        return self != self.NOT_MODIFIED


def get_fields_of_declarative_meta(model_class: type) -> set[str]:
    """
    Получает множество всех полей абстрактной модели BaseModel.
    Нужно для получения всех полей модели apps.core.models.BaseModel

    Отличается от метода get_fields_of_model тем, что не вызывает ошибки

    - sqlalchemy.exc.NoInspectionAvailable:
    No inspection system is available for object of type <class 'sqlalchemy.orm.decl_api.DeclarativeMeta'>
    - sqlalchemy.exc.NoInspectionAvailable:
    No inspection system is available for object of type <class 'sqlalchemy.orm.decl_api.DeclarativeAttributeIntercept'>
    """
    return {field for field, value in model_class.__dict__.items() if isinstance(value, MappedColumn)}


def get_fields_of_model(model_class: type[BaseModel], skip_synonyms_origin: bool) -> list[str]:
    """
    Получает список всех полей модели
    """
    synonym_origins = []
    fields = []

    for field_name, value in inspect(model_class).attrs.items():
        # todo: добавить нормальную поддержку внешних ключей
        # if isinstance(value, Relationship):
        #     ...
        if isinstance(value, RelationshipProperty):
            continue

        if isinstance(value, Synonym):
            synonym_origins.append(value.name)

        fields.append(field_name)

    if skip_synonyms_origin:
        fields = list(filter(lambda v: v not in synonym_origins, fields))

    return fields


async def get_or_create(
    session: AsyncSession,
    model: type[T],
    with_for_update: bool = False,
    defaults: dict[str, Any] | None = None,
    **kwargs,
) -> tuple[T, bool]:
    """
    Аналог get_or_create в django

    https://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create
    """
    stmt = select(model).filter_by(**kwargs)
    if with_for_update:
        stmt = stmt.with_for_update()
    instance: T | None = await session.scalar(stmt)

    if instance is not None:
        return instance, False

    kwargs |= defaults or {}
    instance = model(**kwargs)

    try:
        session.add(instance)

    # The actual exception depends on the specific database, so we catch all IntegrityError exceptions.
    # This is similar to the official documentation:
    # https://docs.sqlalchemy.org/en/latest/orm/session_transaction.html
    except IntegrityError:
        await session.rollback()
        instance = await session.scalar(stmt)
        return cast(T, instance), False

    return instance, True


async def insert_or_update(
    session: AsyncSession,
    model: type[T],
    keys: dict[str, Any],
    other_attr: dict[str, Any],
) -> tuple[T, ReturnState]:
    """
    Создаёт объект, если его не было, обновляет, если требуется, иначе возвращает запись из бд

    Это аналог функции merge из sqlalchemy, но возвращающая статус выполнения

    Args:
        session(AsyncSession): сессия sqlalchemy
        model: модель, объект которой ищется
        keys(dict[str, Any]): ключевые поля, по которым будет производиться поиск элемента в базе
        other_attr(dict[str, Any]): поля, возможно требующие обновления

    Returns:
        tuple[Any, ReturnState]: кортеж из элемента модели и состояния (не изменён, создан или обновлен)
    """
    stmt = select(model).with_for_update(read=True).filter_by(**keys)
    instance = await session.scalar(stmt)

    # Объект в базе не найден => создаём новый
    if instance is None:
        stmt = (
            insert(model)
            .values(**keys, **other_attr)
            .on_conflict_do_update(
                index_elements=list(keys.keys()),
                set_=other_attr,
            )
            .returning(model)
        )
        return cast(T, await session.scalar(stmt)), ReturnState.CREATED

    # Проверяем поля на обновление
    for_update = {field: value for field, value in other_attr.items() if getattr(instance, field) != value}

    # Если ничего не обновлено, то возвращаем объект из базы
    if len(for_update) == 0:
        return instance, ReturnState.NOT_MODIFIED

    # Иначе обновляем
    stmt = update(model).filter_by(**keys).values(**for_update).returning(model)
    return cast(T, await session.scalar(stmt)), ReturnState.UPDATED
