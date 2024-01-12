"""
Аналог ScrollingGroup из aiogram_dialogs, но пагинация происходит на стороне базы данных
"""
from collections.abc import Awaitable, Callable

from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram_dialog.api.entities import ChatEvent
from aiogram_dialog.api.protocols import DialogManager, DialogProtocol
from aiogram_dialog.widgets.common import ManagedWidget, WhenCondition
from aiogram_dialog.widgets.kbd import Group, Keyboard
from aiogram_dialog.widgets.widget_event import (
    WidgetEventProcessor,
    ensure_event_processor,
)

OnStateChanged = Callable[
    [ChatEvent, "ManagedDatabasePaginatedScrollingGroupAdapter", DialogManager],
    Awaitable,
]


# pylint: disable=too-many-ancestors
class DatabasePaginatedScrollingGroup(Group):
    """
    Аналог ScrollingGroup из aiogram_dialogs, но пагинация происходит на стороне базы данных

    В геттере нужно указать поле total, которое будет означать общее число элементов.
    """

    def __init__(  # noqa: D107
        self,
        *buttons: Keyboard,
        id: str,  # pylint: disable=redefined-builtin
        width: int | None = None,
        height: int = 0,
        when: WhenCondition = None,
        on_page_changed: (OnStateChanged | WidgetEventProcessor | None) = None,
        hide_on_single_page: bool = False,
        total_key="total",
    ):
        super().__init__(*buttons, id=id, width=width, when=when)
        self.height = height
        self.on_page_changed = ensure_event_processor(on_page_changed)
        self.hide_on_single_page = hide_on_single_page
        self.total_key = total_key

    # pylint: disable=missing-function-docstring
    async def _render_keyboard(
        self,
        data: dict,
        manager: DialogManager,
    ) -> list[list[InlineKeyboardButton]]:
        kbd = await super()._render_keyboard(data, manager)
        total = data[self.total_key]
        pages = (total + self.height - 1) // self.height
        last_page = pages - 1
        if pages == 0 or (pages == 1 and self.hide_on_single_page):
            return kbd
        current_page = min(last_page, self.get_page(manager))
        next_page = min(last_page, current_page + 1)
        prev_page = max(0, current_page - 1)
        pager = [
            [
                InlineKeyboardButton(
                    text="1",
                    callback_data=self._item_callback_data("0"),
                ),
                InlineKeyboardButton(
                    text="<",
                    callback_data=self._item_callback_data(prev_page),
                ),
                InlineKeyboardButton(
                    text=str(current_page + 1),
                    callback_data=self._item_callback_data(current_page),
                ),
                InlineKeyboardButton(
                    text=">",
                    callback_data=self._item_callback_data(next_page),
                ),
                InlineKeyboardButton(
                    text=str(last_page + 1),
                    callback_data=self._item_callback_data(last_page),
                ),
            ],
        ]

        return kbd + pager

    # pylint: disable=missing-function-docstring
    async def _process_item_callback(
        self,
        callback: CallbackQuery,
        data: str,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        await self.set_page(callback, int(data), manager)
        return True

    # pylint: disable=missing-function-docstring
    def get_page(self, manager: DialogManager) -> int:
        return manager.current_context().widget_data.get(self.widget_id, 0)

    # pylint: disable=missing-function-docstring
    async def set_page(
        self,
        event: ChatEvent,
        page: int,
        manager: DialogManager,
    ) -> None:
        manager.current_context().widget_data[self.widget_id] = page
        await self.on_page_changed.process_event(
            event,
            self.managed(manager),
            manager,
        )

    # pylint: disable=missing-function-docstring
    def managed(self, manager: DialogManager):
        return ManagedDatabasePaginatedScrollingGroupAdapter(self, manager)


# pylint: disable=missing-class-docstring
class ManagedDatabasePaginatedScrollingGroupAdapter(ManagedWidget[DatabasePaginatedScrollingGroup]):
    # pylint: disable=missing-function-docstring
    def get_page(self) -> int:
        return self.widget.get_page(self.manager)

    # pylint: disable=missing-function-docstring
    async def set_page(self, page: int) -> None:
        return await self.widget.set_page(
            self.manager.event,
            page,
            self.manager,
        )
