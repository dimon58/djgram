"""
Геттеры для диалогов
"""
from enum import Enum
from typing import TYPE_CHECKING

from aiogram_dialog import DialogManager
from sqlalchemy import func, select

from djgram.db.utils import get_fields_of_model

from ..base import apps_admins
from .utils import prepare_rows

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from djgram.db.models import BaseModel


# pylint: disable=unused-argument
async def get_apps(**kwargs):
    """
    Геттер возможных приложений
    """

    apps = [(app_id, app.verbose_name) for app_id, app in enumerate(apps_admins)]
    return {
        "apps": apps,
    }


async def get_models(dialog_manager: DialogManager, **kwargs):
    """
    Геттер возможных моделей
    """

    app_id = dialog_manager.dialog_data["app_id"]

    app_admin = apps_admins[app_id]

    models = [(app_id, app.name) for app_id, app in enumerate(app_admin.admin_models)]

    return {
        "models": models,
        "app_name": app_admin.verbose_name,
    }


# pylint: disable=too-many-locals
async def get_rows(dialog_manager: DialogManager, **kwargs):
    """
    Геттер строк для модели
    """

    db_session: AsyncSession = dialog_manager.middleware_data["db_session"]

    app = apps_admins[dialog_manager.dialog_data["app_id"]]
    model_admin = app.admin_models[dialog_manager.dialog_data["model_id"]]

    page: int = dialog_manager.current_context().widget_data.get("rows", 0)

    stmt = (
        select(model_admin.model)
        .order_by(model_admin.model.id.desc())
        .offset(app.rows_per_page * page)
        .limit(app.rows_per_page)
    )
    rows = (await db_session.scalars(stmt)).all()

    data = []

    for row in rows:
        _row = []

        # Обрабатываем колонки вида user__id, т.е. непрямых полей
        for column in model_admin.list_display:
            _value = row
            for chain in column.split("__"):
                _prev_value = _value
                _value = getattr(_value, chain)

                # Если встретилось свойство, то достаём его значение
                if isinstance(_value, property):
                    _value = property.__get__(_value, _prev_value)

            # Превращаем Enum в его значение
            if isinstance(_value, Enum):
                _value = _value.value

            _row.append(_value)

        # Последней колонкой добавляем id
        _row.append(row.id)
        data.append(_row)

    # Отрезаем последнюю колонку id, чтобы передать её, как идентификаторы для виджета Select
    rows = []
    ids = []
    for row in data:
        rows.append(row[:-1])
        ids.append(row[-1])

    rows = list(zip(ids, prepare_rows(rows), strict=True))

    stmt = select(func.count("*")).select_from(model_admin.model)
    total = await db_session.scalar(stmt)

    # Правильные единицы измерения. "Запись" в нужном числе и родительном падеже.
    _total = total % 100

    if 5 <= _total <= 20 or _total % 10 in (0, 5, 6, 7, 8, 9):
        units = "записей"

    elif _total % 10 == 1:
        units = "запись"

    else:
        units = "записи"

    return {
        "rows": rows,
        "app_name": app.verbose_name,
        "model_name": model_admin.name,
        "header": "│".join(model_admin.list_display),
        "total": total,
        "units": units,
    }


async def get_row_detail(dialog_manager: DialogManager, **kwargs):
    """
    Геттер для записи в бд
    """

    db_session: AsyncSession = dialog_manager.middleware_data["db_session"]

    app = apps_admins[dialog_manager.dialog_data["app_id"]]
    model_admin = app.admin_models[dialog_manager.dialog_data["model_id"]]
    row_id = dialog_manager.dialog_data["row_id"]

    model = model_admin.model

    stmt = select(model).where(model.id == row_id)
    row: BaseModel = (await db_session.execute(stmt)).one()[0]

    text = []

    # Рендерим в виде
    # field1: value1
    # field2: value2
    # field3: value3
    # field4: value4
    # field5: value5
    for field in get_fields_of_model(type(row)):
        if not field.startswith("_"):
            text.append(f"<strong>{field}</strong>: {getattr(row, field)}")  # noqa: PERF401

    text = "\n".join(text)
    return {
        "object_name": f"[{row_id}] {model.__name__}",
        "text": text,
        "app_name": app.verbose_name,
        "model_name": model_admin.name,
        "header": "│".join(model_admin.list_display),
    }
