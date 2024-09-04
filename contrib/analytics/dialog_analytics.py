"""
Аналитика взаимодействия пользователей с aiogram dialog


Todo: улучшить взаимодействие с наследниками Keyboard
- [x] Keyboard

- [ ] Button
- [ ] Url
- [ ] WebApp
- [ ] SwitchInlineQuery


- [x] Calendar

- [ ] BaseCheckbox
- [ ] Checkbox

- [ ] Counter

- [ ] Group
- [ ] Group
- [ ] Row
- [ ] Column

- [ ] ListGroup

- [ ] BasePager
- [ ] SwitchPage
- [ ] LastPage
- [ ] NextPage
- [ ] PrevPage
- [ ] FirstPage
- [ ] CurrentPage
- [ ] NumberedPager

- [ ] RequestContact
- [ ] RequestLocation

- [ ] ScrollingGroup
- [ ] DatabasePaginatedScrollingGroup

- [ ] Select
- [ ] StatefulSelect
- [ ] Radio
- [ ] Multiselect
- [ ] Toggle

- [ ] SwitchTo
- [ ] Next
- [ ] Back
- [ ] Cancel
- [ ] Start

- [ ] StubScroll
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Self

import orjson
import pydantic
from aiogram.dispatcher.middlewares.user_context import EVENT_CONTEXT_KEY, EventContext
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, DialogProtocol
from aiogram_dialog.api.internal import CALLBACK_DATA_KEY, CONTEXT_KEY, STACK_KEY
from aiogram_dialog.widgets.kbd import Calendar, Keyboard
from pydantic import ConfigDict

from djgram.configs import ANALYTICS_DIALOG_TABLE
from djgram.contrib.analytics.misc import DIALOG_ANALYTICS_DDL_SQL
from djgram.db import clickhouse
from djgram.system_configs import MIDDLEWARE_AUTH_USER_KEY

if TYPE_CHECKING:
    from aiogram_dialog.api.entities import Context, Stack

logger = logging.getLogger("dialog_analytics")

# Задачи сохранения аналитики в clickhouse
# Временно сохраняем из тут, чтобы сборщик мусора не убил раньше времени
# https://docs.python.org/3.12/library/asyncio-task.html#asyncio.create_task
_pending_tasks = set[asyncio.Task]()


class DialogAnalytics(pydantic.BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: datetime
    update_id: int
    callback_query: str
    processor: str

    # User info
    telegram_user_id: int | None
    telegram_chat_id: int | None
    telegram_thread_id: int | None
    telegram_business_connection_id: int | None
    user_id: int

    # Widget info
    states_group_name: str
    widget_id: str
    widget_type: str
    widget_text: str | None
    # Additional widget info
    calendar_user_config_firstweekday: int | None = None
    calendar_user_config_timezone_name: str | None = None
    calendar_user_config_timezone_offset: int | None = None

    aiogd_original_callback_data: str

    # aiogram_dialog.api.entities.Context
    aiogd_context_intent_id: str
    aiogd_context_stack_id: str
    aiogd_context_state: str
    aiogd_context_start_data: str
    aiogd_context_dialog_data: str
    aiogd_context_widget_data: str

    # aiogram_dialog.api.entities.Stack
    aiogd_stack_id: str
    aiogd_stack_intents: list[str]
    aiogd_stack_last_message_id: int | None
    aiogd_stack_last_reply_keyboard: bool
    aiogd_stack_last_media_id: str | None
    aiogd_stack_last_media_unique_id: str | None
    aiogd_stack_last_income_media_group_id: str | None

    @staticmethod
    def get_user_id(manager: DialogManager) -> int | None:
        user = manager.middleware_data[MIDDLEWARE_AUTH_USER_KEY]
        if user is None:
            return None

        return user.id

    @staticmethod
    def get_widget_text(callback: CallbackQuery, manager: DialogManager) -> str | None:

        if (reply_markup := callback.message.reply_markup) is None:
            return None

        aiogd_original_callback_data = manager.middleware_data[CALLBACK_DATA_KEY]

        for row in reply_markup.inline_keyboard:
            for button in row:
                if button.callback_data == aiogd_original_callback_data:
                    return button.text

        return None

    @classmethod
    def from_callback(
        cls,
        processor: str,
        keyboard: Keyboard,
        callback: CallbackQuery,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> Self:
        event_context: EventContext = manager.middleware_data[EVENT_CONTEXT_KEY]

        aiogd_context: Context = manager.middleware_data[CONTEXT_KEY]
        aiogd_stack: Stack = manager.middleware_data[STACK_KEY]

        return cls(
            date=datetime.now(tz=UTC),
            update_id=manager.middleware_data["event_update"].update_id,
            callback_query=callback.model_dump_json(exclude_unset=True),
            processor=processor,
            # User info
            telegram_user_id=event_context.user_id,
            telegram_chat_id=event_context.chat_id,
            telegram_thread_id=event_context.thread_id,
            telegram_business_connection_id=event_context.business_connection_id,
            user_id=cls.get_user_id(manager),
            # Widget info
            states_group_name=dialog.states_group_name(),
            widget_id=keyboard.widget_id,
            widget_type=type(keyboard).__name__,
            widget_text=cls.get_widget_text(callback, manager),
            aiogd_original_callback_data=manager.middleware_data[CALLBACK_DATA_KEY],
            # aiogram_dialog.api.entities.Context
            aiogd_context_intent_id=aiogd_context.id,
            aiogd_context_stack_id=aiogd_context.stack_id,
            aiogd_context_state=aiogd_context.state.state,
            aiogd_context_start_data=orjson.dumps(aiogd_context.start_data),
            aiogd_context_dialog_data=orjson.dumps(aiogd_context.dialog_data),
            aiogd_context_widget_data=orjson.dumps(aiogd_context.widget_data),
            # aiogram_dialog.api.entities.Stack
            aiogd_stack_id=aiogd_stack.id,
            aiogd_stack_intents=aiogd_stack.intents,
            aiogd_stack_last_message_id=aiogd_stack.last_message_id,
            aiogd_stack_last_reply_keyboard=aiogd_stack.last_reply_keyboard,
            aiogd_stack_last_media_id=aiogd_stack.last_media_id,
            aiogd_stack_last_media_unique_id=aiogd_stack.last_media_unique_id,
            aiogd_stack_last_income_media_group_id=aiogd_stack.last_income_media_group_id,
        )

    async def extend_from_calendar(
        self,
        calendar: Calendar,
        widget_data: dict[str, Any],
        manager: DialogManager,
    ) -> None:
        # noinspection PyProtectedMember
        calendar_user_config = await calendar._get_user_config(widget_data, manager)  # noqa: SLF001

        self.calendar_user_config_firstweekday = calendar_user_config.firstweekday
        self.calendar_user_config_timezone_name = calendar_user_config.timezone.tzname(None)
        self.calendar_user_config_timezone_offset = calendar_user_config.timezone.utcoffset(None).seconds

    async def extend_from(self, keyboard: Keyboard, manager: DialogManager) -> None:

        aiogd_context: Context = manager.middleware_data[CONTEXT_KEY]

        if isinstance(keyboard, Calendar):
            await self.extend_from_calendar(keyboard, aiogd_context.widget_data, manager)
            return

    async def save_to_clickhouse(self) -> None:
        task = asyncio.create_task(clickhouse.safe_insert_dict(ANALYTICS_DIALOG_TABLE, self.model_dump(mode="python")))
        task.add_done_callback(_pending_tasks.remove)
        _pending_tasks.add(task)


async def save_statistics(
    processor: str,
    keyboard: Keyboard,
    callback: CallbackQuery,
    dialog: DialogProtocol,
    manager: DialogManager,
):
    dialog_analytics = DialogAnalytics.from_callback(processor, keyboard, callback, dialog, manager)
    await dialog_analytics.extend_from(keyboard, manager)

    await dialog_analytics.save_to_clickhouse()
    logger.debug(
        "User %s in chat %s clicked on %s in dialog %s (state %s)",
        dialog_analytics.user_id,
        dialog_analytics.telegram_chat_id,
        dialog_analytics.widget_id,
        dialog_analytics.aiogd_context_intent_id,
        dialog_analytics.aiogd_context_state,
    )


async def keyboard_process_callback(
    self: Keyboard,
    callback: CallbackQuery,
    dialog: DialogProtocol,
    manager: DialogManager,
) -> bool:
    if callback.data == self.widget_id:
        await save_statistics("process_own_callback", self, callback, dialog, manager)
        return await self._process_own_callback(
            callback,
            dialog,
            manager,
        )
    prefix = self.callback_prefix()
    if prefix and callback.data.startswith(prefix):
        await save_statistics("process_item_callback", self, callback, dialog, manager)
        return await self._process_item_callback(
            callback,
            callback.data[len(prefix) :],
            dialog,
            manager,
        )
    return await self._process_other_callback(callback, dialog, manager)


def patch_keyboard():
    Keyboard.process_callback = keyboard_process_callback


def setup_dialog_analytics():
    logger.debug("Ensuring clickhouse tables for dialog analytics")
    with open(DIALOG_ANALYTICS_DDL_SQL, encoding="utf-8") as sql_file:  # noqa: PTH123
        task = clickhouse.run_sql_from_sync(sql_file.read())
        task.add_done_callback(_pending_tasks.remove)
        _pending_tasks.add(task)

    patch_keyboard()
