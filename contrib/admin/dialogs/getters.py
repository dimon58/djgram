"""
Геттеры для диалогов
"""

import logging
from typing import TYPE_CHECKING, Any, cast

from aiogram_dialog import DialogManager
from sqlalchemy import func, select
from sqlalchemy.sql import sqltypes

from djgram.db.middlewares import MIDDLEWARE_DB_SESSION_KEY
from ..base import apps_admins
from ..rendering import QUERY_KEY, get_field_by_path, prepare_rows

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from djgram.db.models import BaseModel

logger = logging.getLogger(__name__)


# pylint: disable=unused-argument
async def get_apps(**kwargs) -> dict[str, Any]:
    """
    Геттер возможных приложений
    """

    apps = [(app_id, app.verbose_name) for app_id, app in enumerate(apps_admins) if len(app.admin_models) > 0]
    return {
        "apps": apps,
    }


async def get_models(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    """
    Геттер возможных моделей
    """

    db_session = dialog_manager.middleware_data[MIDDLEWARE_DB_SESSION_KEY]

    app_id = dialog_manager.dialog_data["app_id"]

    app_admin = apps_admins[app_id]

    models = [(app_id, await app.display_name(db_session)) for app_id, app in enumerate(app_admin.admin_models)]

    return {
        "models": models,
        "app_name": app_admin.verbose_name,
    }


# pylint: disable=too-many-locals
async def get_rows(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    """
    Геттер строк для модели
    """

    db_session: AsyncSession = dialog_manager.middleware_data[MIDDLEWARE_DB_SESSION_KEY]

    app = apps_admins[dialog_manager.dialog_data["app_id"]]
    model_admin = app.admin_models[dialog_manager.dialog_data["model_id"]]

    page = cast(int, dialog_manager.current_context().widget_data.get("rows", 0))

    stmt = select(model_admin.model)
    total_stmt = select(func.count()).select_from(model_admin.model)

    if QUERY_KEY in dialog_manager.dialog_data:
        query_filter = model_admin.generate_search_filter(dialog_manager.dialog_data[QUERY_KEY])

        stmt = stmt.where(query_filter)
        total_stmt = total_stmt.where(query_filter)

    stmt = stmt.order_by(model_admin.model.id.desc()).offset(app.rows_per_page * page).limit(app.rows_per_page)
    rows = (await db_session.scalars(stmt)).all()
    total = cast(int, await db_session.scalar(total_stmt))

    data = []

    for row in rows:
        _row = []

        # Обрабатываем колонки вида user__id, т.е. непрямых полей
        for column in model_admin.list_display:
            _value = get_field_by_path(row, column)

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


async def get_search_description(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    app = apps_admins[dialog_manager.dialog_data["app_id"]]
    model_admin = app.admin_models[dialog_manager.dialog_data["model_id"]]

    return {
        "app_name": app.verbose_name,
        "model_name": model_admin.name,
        "description": "Поиск по полям:\n- " + "\n- ".join(model_admin.search_fields),
    }


async def get_row_detail(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    """
    Геттер для записи в бд
    """

    db_session: AsyncSession = dialog_manager.middleware_data[MIDDLEWARE_DB_SESSION_KEY]

    app = apps_admins[dialog_manager.dialog_data["app_id"]]
    model_admin = app.admin_models[dialog_manager.dialog_data["model_id"]]
    row_id = dialog_manager.dialog_data["row_id"]

    model: type[BaseModel] = model_admin.model

    if isinstance(model.id.type, sqltypes.Integer):
        row_id = int(row_id)
    stmt = select(model).where(model.id == row_id)
    obj: BaseModel | None = await db_session.scalar(stmt)
    object_name = f"[{row_id}] {model.__name__}"

    if obj is None:
        logger.error("Not found %s with id = %s", model, row_id)
        return {
            "object_name": object_name,
            "text": "NOT FOUND",
            "app_name": app.verbose_name,
            "model_name": model_admin.name,
        }

    text = []

    for field in model_admin.get_fields_of_model():
        # if not field.startswith("_"):
        text.append(field.render_for_obj(obj, model_admin.show_docs))  # noqa: PERF401

    text = "\n".join(text)
    return {
        "object_name": object_name,
        "text": text,
        "app_name": app.verbose_name,
        "model_name": model_admin.name,
    }
