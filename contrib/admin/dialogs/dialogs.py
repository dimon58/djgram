"""
Диалоги для администрирования
"""
import logging
import operator
import os.path
from typing import TYPE_CHECKING, Any

from aiogram import F
from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.manager.manager import ManagerImpl
from aiogram_dialog.tools import render_transitions
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Cancel,
    Row,
    ScrollingGroup,
    Select,
    SwitchTo,
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
from djgram.contrib.dialogs.utils import delete_last_message_from_dialog_manager

from .callbacks import (
    on_app_selected,
    on_model_selected,
    on_row_selected,
    on_search_row_input,
    reset_page,
)
from .getters import (
    get_apps,
    get_models,
    get_row_detail,
    get_rows,
    get_search_description,
)
from .states import AdminStates

if TYPE_CHECKING:
    from djgram.contrib.auth.models import User
    from djgram.contrib.telegram.models import TelegramUser
logger = logging.getLogger(__name__)


def __log_admin_dialog_interaction(middleware_data, action):
    """
    Логирует взаимодействие с диалогом

    Просто общий кусок кода для on_admin_dialog_start и on_admin_dialog_close

    Args:
        middleware_data(dict): данные посредников telegram
        action: действие с диалогом
    """

    telegram_user: TelegramUser = middleware_data["telegram_user"]
    user: User = middleware_data["user"]

    full_name: str = telegram_user.get_full_name()
    logger.info(
        f"{action} admin dialog with user [id={user.id}] "
        f"[telegram_id={telegram_user.id}, username={telegram_user.username}] "
        f"{full_name}",
    )


# pylint: disable=unused-argument
async def on_admin_dialog_start(result: Any, dialog_manager: DialogManager):
    """
    Обработчик начала диалога администрирования

    Просто логирует, что диалог начался
    """
    __log_admin_dialog_interaction(dialog_manager.middleware_data, "Start")


# pylint: disable=unused-argument
async def on_admin_dialog_close(result: Any, dialog_manager: ManagerImpl):
    """
    Обработчик закрытия диалога администрирования

    Удаляет сообщение администрирования и логирует, что диалог окончен
    """
    __log_admin_dialog_interaction(dialog_manager.middleware_data, "Close")

    await delete_last_message_from_dialog_manager(dialog_manager)


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
            id="rows",
            width=1,
            height=ADMIN_ROWS_PER_PAGE,
            hide_on_single_page=True,
        ),
        SwitchTo(Const("🔍 Поиск"), id="search", state=AdminStates.search_row, when=F["search_enable"]),
        Row(Back(Const("\u25c0 Назад"), on_click=reset_page), Cancel(Const("\u23f9 Завершить"))),
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
        Row(Back(Const("\u25c0 Назад"), on_click=reset_page), Cancel(Const("\u23f9 Завершить"))),
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
            SwitchTo(Const("\u25c0 Назад"), id="back_to_row_select", state=AdminStates.row_list),
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
    render_transitions(
        admin_dialog,
        title="Admin dialog",
        filename=os.path.join(DIALOG_DIAGRAMS_DIR, "admin_dialog"),  # noqa: PTH118
    )
    logger.info("Generated diagram for admin dialog")
