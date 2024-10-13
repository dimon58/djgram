"""
Геттеры для диалогов
"""

import html
import logging
from typing import TYPE_CHECKING, Any, TypeVar, cast

from aiogram_dialog import DialogManager
from sqlalchemy import func, select
from sqlalchemy.sql import sqltypes

from djgram.contrib.dialogs.database_paginated_scrolling_group import DEFAULT_TOTAL_KEY, DatabasePaginatedScrollingGroup
from djgram.db.models import BaseModel
from djgram.system_configs import MIDDLEWARE_DB_SESSION_KEY

from ..base import AppAdmin, ModelAdmin, apps_admins
from ..rendering import QUERY_KEY, get_field_by_path, prepare_rows

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T", bound=BaseModel)

APP_ID_KEY = "app_id"
MODEL_ID_KEY = "model_id"
ROW_ID_KEY = "row_id"

APPS_KEY = "apps"
MODELS_KEY = "models"

APPS_NAME_KEY = "app_name"
MODEL_NAME_KEY = "model_name"
PAGE_KEY = "page"
OBJECT_NAME_KEY = "object_name"

TEXT_KEY = "text"
OBJECT_ACTION_BUTTONS_KEY = "object_action_buttons"

ROWS_KEY = "rows"
HEADER_KEY = "header"
UNITS_KEY = "units"
SEARCH_ENABLE_KEY = "search_enable"
DESCRIPTION_KEY = "description"

logger = logging.getLogger(__name__)


# pylint: disable=unused-argument
async def get_apps(**kwargs) -> dict[str, Any]:
    """
    Геттер возможных приложений
    """

    apps = [(app_id, app.verbose_name) for app_id, app in enumerate(apps_admins) if len(app.admin_models) > 0]
    return {
        APPS_KEY: apps,
    }


async def get_models(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    """
    Геттер возможных моделей
    """

    db_session = dialog_manager.middleware_data[MIDDLEWARE_DB_SESSION_KEY]

    app_id = dialog_manager.dialog_data[APP_ID_KEY]

    app_admin = apps_admins[app_id]

    models = [(app_id, await app.display_name(db_session)) for app_id, app in enumerate(app_admin.admin_models)]

    return {
        MODELS_KEY: models,
        APPS_NAME_KEY: html.escape(app_admin.verbose_name),
    }


# pylint: disable=too-many-locals
async def get_rows(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    """
    Геттер строк для модели
    """

    db_session: AsyncSession = dialog_manager.middleware_data[MIDDLEWARE_DB_SESSION_KEY]

    app = apps_admins[dialog_manager.dialog_data[APP_ID_KEY]]
    model_admin = app.admin_models[dialog_manager.dialog_data[MODEL_ID_KEY]]

    page = DatabasePaginatedScrollingGroup.get_page_number_from_manager(dialog_manager, PAGE_KEY)

    stmt = select(model_admin.model)
    total_stmt = select(func.count()).select_from(model_admin.model)

    if QUERY_KEY in dialog_manager.dialog_data:
        query_filter = model_admin.generate_search_filter(dialog_manager.dialog_data[QUERY_KEY])

        stmt = stmt.where(query_filter)
        total_stmt = total_stmt.where(query_filter)

    stmt = stmt.order_by(model_admin.ordering).offset(app.rows_per_page * page).limit(app.rows_per_page)
    rows = (await db_session.scalars(stmt)).all()
    total = cast(int, await db_session.scalar(total_stmt))

    data = []

    for row in rows:
        _row = []

        # Обрабатываем колонки вида user__id, т.е. непрямых полей
        for column in model_admin.list_display:
            if column.startswith("call:"):
                need_call = True
                column = column[5:]  # noqa: PLW2901
            else:
                need_call = False

            _value = get_field_by_path(row, column)

            if need_call:
                _value = _value()

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

    if 5 <= _total <= 20 or _total % 10 in (0, 5, 6, 7, 8, 9):  # noqa: PLR2004
        units = "записей"

    elif _total % 10 == 1:
        units = "запись"

    else:
        units = "записи"

    return {
        ROWS_KEY: rows,
        APPS_NAME_KEY: html.escape(app.verbose_name),
        MODEL_NAME_KEY: html.escape(model_admin.name),
        HEADER_KEY: "│".join(model_admin.list_display),
        DEFAULT_TOTAL_KEY: total,
        UNITS_KEY: units,
        SEARCH_ENABLE_KEY: len(model_admin.search_fields) > 0,
    }


async def get_search_description(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    app = apps_admins[dialog_manager.dialog_data[APP_ID_KEY]]
    model_admin = app.admin_models[dialog_manager.dialog_data[MODEL_ID_KEY]]

    return {
        APPS_NAME_KEY: html.escape(app.verbose_name),
        MODEL_NAME_KEY: html.escape(model_admin.name),
        DESCRIPTION_KEY: html.escape("Поиск по полям:\n- " + "\n- ".join(model_admin.search_fields)),
    }


async def get_admin_object_detail_context(
    dialog_manager: DialogManager,
) -> tuple[AppAdmin, type[T], type[ModelAdmin], T | None, Any]:
    db_session: AsyncSession = dialog_manager.middleware_data[MIDDLEWARE_DB_SESSION_KEY]

    app: AppAdmin = apps_admins[dialog_manager.dialog_data[APP_ID_KEY]]
    model_admin: type[ModelAdmin] = app.admin_models[dialog_manager.dialog_data[MODEL_ID_KEY]]
    row_id: Any = dialog_manager.dialog_data[ROW_ID_KEY]

    model: type[T] = model_admin.model  # pyright: ignore [reportAssignmentType]

    if isinstance(model.id.type, sqltypes.Integer):
        row_id = int(row_id)

    stmt = select(model).where(model.id == row_id)
    obj: T | None = await db_session.scalar(stmt)

    return app, model, model_admin, obj, row_id


async def get_row_detail(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    """
    Геттер для записи в бд
    """

    app, model, model_admin, obj, row_id = await get_admin_object_detail_context(dialog_manager)

    if obj is None:
        logger.error("Not found %s with id = %s", model, row_id)
        return {
            OBJECT_NAME_KEY: html.escape(f"{model.__name__}<{row_id}>"),
            TEXT_KEY: "NOT FOUND",
            APPS_NAME_KEY: html.escape(app.verbose_name),
            MODEL_NAME_KEY: html.escape(model_admin.name),
        }

    text = []

    for field in model_admin.get_fields_widgets():
        # if not field.startswith("_"):
        text.append(field.render_for_obj(obj, model_admin.show_docs))  # noqa: PERF401

    text = "\n".join(text)
    return {
        OBJECT_NAME_KEY: html.escape(str(obj)),
        TEXT_KEY: text,
        APPS_NAME_KEY: html.escape(app.verbose_name),
        MODEL_NAME_KEY: html.escape(model_admin.name),
        OBJECT_ACTION_BUTTONS_KEY: [
            (button.button_id, button.get_title(obj))
            for button in model_admin.object_action_buttons
            if button.should_render(obj, dialog_manager.middleware_data)
        ],
    }
