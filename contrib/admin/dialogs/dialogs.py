"""
Диалоги для администрирования
"""

import logging
import operator
import os.path

from aiogram import F
from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Cancel,
    Row,
    ScrollingGroup,
    Select,
    SwitchTo,
    Button,
)
from aiogram_dialog.widgets.text import Const, Format

from djgram.configs import (
    ADMIN_APPS_PER_PAGE,
    ADMIN_MODELS_PER_PAGE,
    ADMIN_ROWS_PER_PAGE,
    DIALOG_DIAGRAMS_DIR,
    ENABLE_DIALOG_DIAGRAMS_GENERATION,
)
from djgram.contrib.dialogs.database_paginated_scrolling_group import (
    DatabasePaginatedScrollingGroup,
)
from djgram.utils.diagrams import render_transitions_safe

from .callbacks import (
    on_admin_dialog_close,
    on_admin_dialog_start,
    on_app_selected,
    on_model_selected,
    on_row_selected,
    on_search_row_input,
    reset_page,
    reset_search_query,
)
from .getters import (
    get_apps,
    get_models,
    get_row_detail,
    get_rows,
    get_search_description,
)
from .states import AdminStates
from ..rendering import QUERY_KEY

logger = logging.getLogger(__name__)

admin_dialog = Dialog(
    # Выбор приложения
    Window(
        Const("Администрирование"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="app_id",
                item_id_getter=operator.itemgetter(0),
                items="apps",
                on_click=on_app_selected,
            ),
            id="apps",
            width=1,
            height=ADMIN_APPS_PER_PAGE,
            hide_on_single_page=True,
        ),
        Cancel(Const("\u23f9 Завершить")),
        getter=get_apps,
        state=AdminStates.app_list,
        preview_add_transitions=[
            SwitchTo(Const("model_list"), "model_list", state=AdminStates.model_list),
        ],
    ),
    # Выбор модели
    Window(
        Format("Администрирование"),
        Format("->{app_name}"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="model_id",
                item_id_getter=operator.itemgetter(0),
                items="models",
                on_click=on_model_selected,
            ),
            id="models",
            width=1,
            height=ADMIN_MODELS_PER_PAGE,
            hide_on_single_page=True,
        ),
        Row(Back(Const("\u25c0 Назад")), Cancel(Const("\u23f9 Завершить"))),
        getter=get_models,
        state=AdminStates.model_list,
        preview_add_transitions=[
            SwitchTo(Const("row_list"), "row_list", state=AdminStates.row_list),
        ],
    ),
    # Выбор строки
    Window(
        Format("Администрирование"),
        Format("->{app_name}"),
        Format("->->{model_name}"),
        Format("\nВсего {total} {units}\n"),
        Format("{header}"),
        DatabasePaginatedScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="row_id",
                item_id_getter=operator.itemgetter(0),
                items="rows",
                on_click=on_row_selected,
            ),
            id="page",
            width=1,
            height=ADMIN_ROWS_PER_PAGE,
            hide_on_single_page=True,
        ),
        SwitchTo(
            Const("🔍 Поиск"),
            id="search",
            state=AdminStates.search_row,
            when=F["search_enable"],
        ),
        Button(
            Const("↺ Сбросить поисковый запрос"),
            id="reset_search_query",
            on_click=reset_search_query,
            when=F["dialog_data"][QUERY_KEY],
        ),
        Row(
            Back(Const("\u25c0 Назад"), on_click=reset_page),
            Cancel(Const("\u23f9 Завершить")),
        ),
        getter=get_rows,
        state=AdminStates.row_list,
        preview_add_transitions=[
            SwitchTo(Const("row_detail"), "row_detail", state=AdminStates.row_detail),
        ],
    ),
    # Поиск строки
    Window(
        Format("Администрирование"),
        Format("->{app_name}"),
        Format("->->{model_name}"),
        Format("\nВведите поисковый запрос\n\n{description}"),
        MessageInput(on_search_row_input),
        Row(
            Back(Const("\u25c0 Назад"), on_click=reset_page),
            Cancel(Const("\u23f9 Завершить")),
        ),
        getter=get_search_description,
        state=AdminStates.search_row,
        preview_add_transitions=[
            SwitchTo(Const("row_detail"), "row_detail", state=AdminStates.row_detail),
        ],
    ),
    # Детальный вид записи
    Window(
        Format("Администрирование"),
        Format("->{app_name}"),
        Format("->->{model_name}"),
        Format("->->->{object_name}"),
        Format("\n{text}"),
        Row(
            SwitchTo(
                Const("\u25c0 Назад"),
                id="back_to_row_select",
                state=AdminStates.row_list,
            ),
            Cancel(Const("\u23f9 Завершить")),
        ),
        getter=get_row_detail,
        state=AdminStates.row_detail,
        parse_mode=ParseMode.HTML,
    ),
    on_start=on_admin_dialog_start,
    on_close=on_admin_dialog_close,
)

if ENABLE_DIALOG_DIAGRAMS_GENERATION:
    render_transitions_safe(
        admin_dialog,
        title="Admin dialog",
        filename=os.path.join(DIALOG_DIAGRAMS_DIR, "admin_dialog"),  # noqa: PTH118
    )
    logger.info("Generated diagram for admin dialog")
