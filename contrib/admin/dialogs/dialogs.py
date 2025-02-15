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
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Column, Row, ScrollingGroup, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from djgram.configs import (
    ADMIN_APPS_PER_PAGE,
    ADMIN_MODELS_PER_PAGE,
    ADMIN_ROWS_PER_PAGE,
    DIALOG_DIAGRAMS_DIR,
    ENABLE_DIALOG_DIAGRAMS_GENERATION,
)
from djgram.contrib.dialogs.database_paginated_scrolling_group import DEFAULT_TOTAL_KEY, DatabasePaginatedScrollingGroup
from djgram.utils.diagrams import render_transitions_safe

from ..rendering import QUERY_KEY
from . import getters
from .callbacks import (
    handle_object_action_button,
    on_admin_dialog_close,
    on_admin_dialog_start,
    on_app_selected,
    on_model_selected,
    on_row_selected,
    on_search_row_input,
    reset_page,
    reset_search_query,
)
from .states import AdminStates

logger = logging.getLogger(__name__)

admin_dialog = Dialog(
    # Выбор приложения
    Window(
        Const("Администрирование"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id=getters.APP_ID_KEY,
                item_id_getter=operator.itemgetter(0),
                items=getters.APPS_KEY,
                on_click=on_app_selected,
            ),
            id=getters.APPS_KEY,
            width=1,
            height=ADMIN_APPS_PER_PAGE,
            hide_on_single_page=True,
        ),
        Cancel(Const("\u23f9 Завершить")),
        getter=getters.get_apps,
        state=AdminStates.app_list,
        preview_add_transitions=[
            SwitchTo(Const("model_list"), "model_list", state=AdminStates.model_list),
        ],
        disable_web_page_preview=True,
    ),
    # Выбор модели
    Window(
        Format("Администрирование"),
        Format(f"->{{{getters.APPS_NAME_KEY}}}"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id=getters.MODEL_ID_KEY,
                item_id_getter=operator.itemgetter(0),
                items=getters.MODELS_KEY,
                on_click=on_model_selected,
            ),
            id=getters.MODELS_KEY,
            width=1,
            height=ADMIN_MODELS_PER_PAGE,
            hide_on_single_page=True,
        ),
        Row(Back(Const("\u25c0 Назад")), Cancel(Const("\u23f9 Завершить"))),
        getter=getters.get_models,
        state=AdminStates.model_list,
        preview_add_transitions=[
            SwitchTo(Const("row_list"), "row_list", state=AdminStates.row_list),
        ],
        disable_web_page_preview=True,
    ),
    # Выбор строки
    Window(
        Format("Администрирование"),
        Format(f"->{{{getters.APPS_NAME_KEY}}}"),
        Format(f"->->{{{getters.MODEL_NAME_KEY}}}"),
        Format(f"\nВсего {{{DEFAULT_TOTAL_KEY}}} {{{getters.UNITS_KEY}}}\n"),
        Format("{header}"),
        DatabasePaginatedScrollingGroup(
            Select(
                Format("{item[1]}"),
                id=getters.ROW_ID_KEY,
                item_id_getter=operator.itemgetter(0),
                items=getters.ROWS_KEY,
                on_click=on_row_selected,
            ),
            id=getters.PAGE_KEY,
            width=1,
            height=ADMIN_ROWS_PER_PAGE,
            hide_on_single_page=True,
            total_key=DEFAULT_TOTAL_KEY,
        ),
        SwitchTo(
            Const("🔍 Поиск"),
            id="search",
            state=AdminStates.search_row,
            when=F[getters.SEARCH_ENABLE_KEY],
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
        getter=getters.get_rows,
        state=AdminStates.row_list,
        preview_add_transitions=[
            SwitchTo(Const("row_detail"), "row_detail", state=AdminStates.row_detail),
        ],
        disable_web_page_preview=True,
    ),
    # Поиск строки
    Window(
        Format("Администрирование"),
        Format(f"->{{{getters.APPS_NAME_KEY}}}"),
        Format(f"->->{{{getters.MODEL_NAME_KEY}}}"),
        Format(f"\nВведите поисковый запрос\n\n{{{getters.DESCRIPTION_KEY}}}"),
        MessageInput(on_search_row_input),
        Row(
            Back(Const("\u25c0 Назад"), on_click=reset_page),
            Cancel(Const("\u23f9 Завершить")),
        ),
        getter=getters.get_search_description,
        state=AdminStates.search_row,
        preview_add_transitions=[
            SwitchTo(Const("row_detail"), "row_detail", state=AdminStates.row_detail),
        ],
        disable_web_page_preview=True,
    ),
    # Детальный вид записи
    Window(
        Format("Администрирование"),
        Format(f"->{{{getters.APPS_NAME_KEY}}}"),
        Format(f"->->{{{getters.MODEL_NAME_KEY}}}"),
        Format(f"->->->{{{getters.OBJECT_NAME_KEY}}}"),
        Format("\n{text}"),
        Column(
            Select(
                Format("{item[1]}"),
                id="object_action_button_id",
                item_id_getter=operator.itemgetter(0),
                items=getters.OBJECT_ACTION_BUTTONS_KEY,
                on_click=handle_object_action_button,
            ),
        ),
        Row(
            SwitchTo(
                Const("\u25c0 Назад"),
                id="back_to_row_select",
                state=AdminStates.row_list,
            ),
            Cancel(Const("\u23f9 Завершить")),
        ),
        getter=getters.get_row_detail,
        state=AdminStates.row_detail,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
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
