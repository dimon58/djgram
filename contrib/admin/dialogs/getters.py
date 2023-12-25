"""
Геттеры для диалогов
"""
from enum import Enum
from typing import TYPE_CHECKING

from aiogram_dialog import DialogManager
from sqlalchemy import Column, func, select

from djgram.db.models import BaseModel

from ..base import apps_admins
from .utils import QUERY_KEY, html_escape, prepare_rows

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


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

    db_session = dialog_manager.middleware_data["db_session"]

    app_id = dialog_manager.dialog_data["app_id"]

    app_admin = apps_admins[app_id]

    models = [(app_id, await app.display_name(db_session)) for app_id, app in enumerate(app_admin.admin_models)]

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

    stmt = select(model_admin.model)
    total_stmt = select(func.count("*")).select_from(model_admin.model)

    if QUERY_KEY in dialog_manager.dialog_data:
        query_filter = model_admin.generate_search_filter(dialog_manager.dialog_data[QUERY_KEY])

        stmt = stmt.where(query_filter)
        total_stmt = total_stmt.where(query_filter)

    stmt = stmt.order_by(model_admin.model.id.desc()).offset(app.rows_per_page * page).limit(app.rows_per_page)
    rows = (await db_session.scalars(stmt)).all()
    total = await db_session.scalar(total_stmt)

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
        "search_enable": len(model_admin.search_fields) > 0,
    }


async def get_search_description(dialog_manager: DialogManager, **kwargs):
    app = apps_admins[dialog_manager.dialog_data["app_id"]]
    model_admin = app.admin_models[dialog_manager.dialog_data["model_id"]]

    return {
        "app_name": app.verbose_name,
        "model_name": model_admin.name,
        "description": "Поиск по полям:\n- " + "\n- ".join(model_admin.search_fields),
    }


def render_row_field(obj: BaseModel, field: str, render_docs: bool) -> str:
    res = [f"<strong>{field}</strong>"]

    if render_docs:
        column: Column = getattr(obj.__class__, field)
        doc = getattr(column, "doc", None)  # У Relationship нет документации
        if doc is not None:
            res.append(f"<i>{html_escape(doc)}</i>")

    res.append(f"<pre>{html_escape(getattr(obj, field))}</pre>")

    return "\n".join(res)


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
    obj = await db_session.scalar(stmt)

    text = []

    for field in model_admin.get_fields_of_model():
        # if not field.startswith("_"):
        text.append(render_row_field(obj, field, model_admin.show_docs))  # noqa: PERF401

    text = "\n".join(text)
    return {
        "object_name": f"[{row_id}] {model.__name__}",
        "text": text,
        "app_name": app.verbose_name,
        "model_name": model_admin.name,
    }
