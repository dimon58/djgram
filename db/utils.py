"""
Утилиты для работы с базой данных
"""
import logging
from enum import Enum
from typing import Any

from sqlalchemy import Column, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from djgram.db.models import BaseModel

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


def get_fields_of_declarative_meta(model_class: BaseModel):
    """
    Получает множество всех полей абстрактной модели BaseModel.
    Нужно для получения всех полей модели apps.core.models.BaseModel
    """
    return {field for field, value in model_class.__dict__.items() if isinstance(value, Column)}


def get_fields_of_model(model_class: BaseModel):
    """
    Получает множество всех полей модели
    """
    return {field for field, value in model_class.__dict__.items() if isinstance(value, InstrumentedAttribute)}


async def get_or_create(
    session: AsyncSession,
    model: type[BaseModel],
    defaults: dict[str, Any] | None = None,
    **kwargs,
) -> tuple[BaseModel, bool]:
    """
    Аналог get_or_create в django

    https://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create
    """
    stmt = select(model).filter_by(**kwargs)
    instance: BaseModel | None = await session.scalar(stmt)

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
        return instance, False

    return instance, True


async def insert_or_update(
    session: AsyncSession,
    model: type[BaseModel],
    keys: dict[str, Any],
    other_attr: dict[str, Any],
) -> tuple[BaseModel, ReturnState]:
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
        return await session.scalar(stmt), ReturnState.CREATED

    # Проверяем поля на обновление
    for_update = {}
    for field, value in other_attr.items():
        if getattr(instance, field) != value:
            for_update[field] = value

    # Если ничего не обновлено, то возвращаем объект из базы
    if len(for_update) == 0:
        return instance, ReturnState.NOT_MODIFIED

    # Иначе обновляем
    stmt = update(model).filter_by(**keys).values(**for_update).returning(model)
    return await session.scalar(stmt), ReturnState.UPDATED
