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
import copy
import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Self

import orjson
import pydantic
from aiogram.dispatcher.middlewares.user_context import EVENT_CONTEXT_KEY, EventContext
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, DialogProtocol
from aiogram_dialog.api.entities import Context, Stack
from aiogram_dialog.api.internal import CALLBACK_DATA_KEY, CONTEXT_KEY, STACK_KEY
from aiogram_dialog.widgets.common import Actionable
from aiogram_dialog.widgets.input import BaseInput, MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Calendar, Keyboard
from pydantic import ConfigDict

from djgram.configs import ANALYTICS_DIALOG_TABLE
from djgram.contrib.analytics.misc import DIALOG_ANALYTICS_DDL_SQL
from djgram.db import clickhouse
from djgram.system_configs import MIDDLEWARE_AUTH_USER_KEY
from djgram.utils.misc import suppress_decorator_async

if TYPE_CHECKING:
    from aiogram.fsm.state import State

logger = logging.getLogger("dialog_analytics")

# Задачи сохранения аналитики в clickhouse
# Временно сохраняем из тут, чтобы сборщик мусора не убил раньше времени
# https://docs.python.org/3.12/library/asyncio-task.html#asyncio.create_task
_pending_tasks = set[asyncio.Task]()

DIALOG_ANALYTICS_ENABLED = False


class DialogAnalytics(pydantic.BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: datetime
    update_id: int
    callback_query: str | None = None
    message: str | None = None
    processor: str
    processed: bool
    process_time: float | None = None
    not_processed_reason: str | None = None

    # User info
    telegram_user_id: int | None = None
    telegram_chat_id: int | None = None
    telegram_thread_id: int | None = None
    telegram_business_connection_id: int | None = None
    user_id: int | None = None

    # Widget info
    # Если отправить сообщение, когда в текущем состоянии диалога нет виджета ввода,
    # тогда отправляется в виртуальный MessageInput с widget_id = None
    widget_id: str | None = None
    widget_type: str
    widget_text: str | None = None
    # Additional widget info
    calendar_user_config_firstweekday: int | None = None
    calendar_user_config_timezone_name: str | None = None
    calendar_user_config_timezone_offset: int | None = None

    aiogd_original_callback_data: str | None = None

    # aiogram_dialog.api.entities.Context
    aiogd_context_intent_id: str
    aiogd_context_stack_id: str
    aiogd_context_state: str
    aiogd_context_state_group_name: str
    aiogd_context_start_data: str
    aiogd_context_dialog_data: str
    aiogd_context_widget_data: str

    # aiogram_dialog.api.entities.Stack
    aiogd_stack_id: str
    aiogd_stack_intents: list[str]
    aiogd_stack_last_message_id: int | None = None
    aiogd_stack_last_reply_keyboard: bool
    aiogd_stack_last_media_id: str | None = None
    aiogd_stack_last_media_unique_id: str | None = None
    aiogd_stack_last_income_media_group_id: str | None = None

    # После выполнения кода обработчика
    # aiogram_dialog.api.entities.Context
    # Нового контекста может не быть, например когда пользователь кликнул кнопку завершить
    aiogd_context_intent_id_new: str | None = None
    aiogd_context_stack_id_new: str | None = None
    aiogd_context_state_new: str | None = None
    aiogd_context_state_group_name_new: str | None = None
    aiogd_context_start_data_new: str | None = None
    aiogd_context_dialog_data_new: str | None = None
    aiogd_context_widget_data_new: str | None = None

    # aiogram_dialog.api.entities.Stack
    aiogd_stack_id_new: str
    aiogd_stack_intents_new: list[str]
    aiogd_stack_last_message_id_new: int | None = None
    aiogd_stack_last_reply_keyboard_new: bool
    aiogd_stack_last_media_id_new: str | None = None
    aiogd_stack_last_media_unique_id_new: str | None = None
    aiogd_stack_last_income_media_group_id_new: str | None = None

    @staticmethod
    def get_user_id(manager: DialogManager) -> int | None:
        user = manager.middleware_data[MIDDLEWARE_AUTH_USER_KEY]
        if user is None:
            return None

        return user.id

    @staticmethod
    def get_widget_text(callback: CallbackQuery | None, manager: DialogManager) -> str | None:

        if callback is None:
            return None

        if (reply_markup := callback.message.reply_markup) is None:
            return None

        aiogd_original_callback_data = manager.middleware_data[CALLBACK_DATA_KEY]

        for row in reply_markup.inline_keyboard:
            for button in row:
                if button.callback_data == aiogd_original_callback_data:
                    return button.text

        return None

    @classmethod
    def from_event(
        cls,
        processor: str,
        processed: bool,
        process_time: float | None,
        not_processed_reason: str | None,
        widget: Actionable,
        callback: CallbackQuery | None,
        message: Message | None,
        manager: DialogManager,
        aiogd_context_before: Context,
        aiogd_stack_before: Stack,
    ) -> Self:
        event_context: EventContext = manager.middleware_data[EVENT_CONTEXT_KEY]

        aiogd_context_new: Context = manager.middleware_data[CONTEXT_KEY]
        aiogd_stack_new: Stack = manager.middleware_data[STACK_KEY]

        aiogd_context_state_new: State | None = getattr(aiogd_context_new, "state", None)
        if aiogd_context_state_new is not None:
            aiogd_context_state_group_name_new = aiogd_context_state_new._group.__full_group_name__  # noqa: SLF001
        else:
            aiogd_context_state_group_name_new = None

        # noinspection PyProtectedMember
        return cls(
            date=datetime.now(tz=UTC),
            update_id=manager.middleware_data["event_update"].update_id,
            callback_query=callback.model_dump_json(exclude_unset=True) if callback is not None else None,
            message=message.model_dump_json(exclude_unset=True) if message is not None else None,
            processor=processor,
            processed=processed,
            process_time=process_time,
            not_processed_reason=not_processed_reason,
            # User info
            telegram_user_id=event_context.user_id,
            telegram_chat_id=event_context.chat_id,
            telegram_thread_id=event_context.thread_id,
            telegram_business_connection_id=event_context.business_connection_id,
            user_id=cls.get_user_id(manager),
            # Widget info
            widget_id=widget.widget_id,
            widget_type=type(widget).__name__,
            widget_text=cls.get_widget_text(callback, manager),
            aiogd_original_callback_data=manager.middleware_data.get(CALLBACK_DATA_KEY),
            # aiogram_dialog.api.entities.Context
            aiogd_context_intent_id=aiogd_context_before.id,
            aiogd_context_stack_id=aiogd_context_before.stack_id,
            aiogd_context_state=aiogd_context_before.state.state,
            aiogd_context_state_group_name=aiogd_context_before.state._group.__full_group_name__,  # noqa: SLF001
            aiogd_context_start_data=orjson.dumps(aiogd_context_before.start_data),
            aiogd_context_dialog_data=orjson.dumps(aiogd_context_before.dialog_data),
            aiogd_context_widget_data=orjson.dumps(aiogd_context_before.widget_data),
            # aiogram_dialog.api.entities.Stack
            aiogd_stack_id=aiogd_stack_before.id,
            aiogd_stack_intents=aiogd_stack_before.intents,
            aiogd_stack_last_message_id=aiogd_stack_before.last_message_id,
            aiogd_stack_last_reply_keyboard=aiogd_stack_before.last_reply_keyboard,
            aiogd_stack_last_media_id=aiogd_stack_before.last_media_id,
            aiogd_stack_last_media_unique_id=aiogd_stack_before.last_media_unique_id,
            aiogd_stack_last_income_media_group_id=aiogd_stack_before.last_income_media_group_id,
            # После выполнения кода обработчика
            # aiogram_dialog.api.entities.Context
            # Нового контекста может не быть, например когда пользователь кликнул кнопку завершить
            aiogd_context_intent_id_new=getattr(aiogd_context_new, "id", None),
            aiogd_context_stack_id_new=getattr(aiogd_context_new, "stack_id", None),
            aiogd_context_state_new=getattr(aiogd_context_state_new, "state", None),
            aiogd_context_state_group_name_new=aiogd_context_state_group_name_new,
            aiogd_context_start_data_new=orjson.dumps(getattr(aiogd_context_new, "start_data", None)),
            aiogd_context_dialog_data_new=orjson.dumps(getattr(aiogd_context_new, "dialog_data", None)),
            aiogd_context_widget_data_new=orjson.dumps(getattr(aiogd_context_new, "widget_data", None)),
            # aiogram_dialog.api.entities.Stack
            aiogd_stack_id_new=aiogd_stack_new.id,
            aiogd_stack_intents_new=aiogd_stack_new.intents,
            aiogd_stack_last_message_id_new=aiogd_stack_new.last_message_id,
            aiogd_stack_last_reply_keyboard_new=aiogd_stack_new.last_reply_keyboard,
            aiogd_stack_last_media_id_new=aiogd_stack_new.last_media_id,
            aiogd_stack_last_media_unique_id_new=aiogd_stack_new.last_media_unique_id,
            aiogd_stack_last_income_media_group_id_new=aiogd_stack_new.last_income_media_group_id,
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


@suppress_decorator_async(Exception, logging_level=logging.ERROR)
async def save_keyboard_statistics(
    processor: str,
    processed: bool,
    process_time: float,
    keyboard: Keyboard,
    callback: CallbackQuery,
    manager: DialogManager,
    aiogd_context_before: Context,
    aiogd_stack_before: Stack,
):
    dialog_analytics = DialogAnalytics.from_event(
        processor=processor,
        processed=processed,
        process_time=process_time,
        not_processed_reason=None,
        widget=keyboard,
        callback=callback,
        message=None,
        manager=manager,
        aiogd_context_before=aiogd_context_before,
        aiogd_stack_before=aiogd_stack_before,
    )
    await dialog_analytics.extend_from(keyboard, manager)

    await dialog_analytics.save_to_clickhouse()
    logger.info(
        "User %s in chat %s clicked on %s %s in dialog %s (state %s)",
        dialog_analytics.user_id,
        dialog_analytics.telegram_chat_id,
        dialog_analytics.widget_type,
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
        aiogd_context_before: Context = copy.deepcopy(manager.middleware_data[CONTEXT_KEY])
        aiogd_stack_before: Stack = copy.deepcopy(manager.middleware_data[STACK_KEY])

        start = time.perf_counter()
        processed = await self._process_own_callback(
            callback,
            dialog,
            manager,
        )
        end = time.perf_counter()
        await save_keyboard_statistics(
            processor="process_own_callback",
            processed=processed,
            process_time=end - start,
            keyboard=self,
            callback=callback,
            manager=manager,
            aiogd_context_before=aiogd_context_before,
            aiogd_stack_before=aiogd_stack_before,
        )
        return processed

    prefix = self.callback_prefix()
    if prefix and callback.data.startswith(prefix):
        aiogd_context_before: Context = copy.deepcopy(manager.middleware_data[CONTEXT_KEY])
        aiogd_stack_before: Stack = copy.deepcopy(manager.middleware_data[STACK_KEY])

        start = time.perf_counter()
        processed = await self._process_item_callback(
            callback,
            callback.data[len(prefix) :],
            dialog,
            manager,
        )
        end = time.perf_counter()
        await save_keyboard_statistics(
            processor="process_item_callback",
            processed=processed,
            process_time=end - start,
            keyboard=self,
            callback=callback,
            manager=manager,
            aiogd_context_before=aiogd_context_before,
            aiogd_stack_before=aiogd_stack_before,
        )

        return processed
    return await self._process_other_callback(callback, dialog, manager)


def patch_keyboard():
    Keyboard.process_callback = keyboard_process_callback


@suppress_decorator_async(Exception, logging_level=logging.ERROR)
async def save_input_statistics(
    processor: str,
    processed: bool,
    process_time: float | None,
    not_processed_reason: str | None,
    input_: BaseInput,
    message: Message,
    manager: DialogManager,
    aiogd_context_before: Context,
    aiogd_stack_before: Stack,
):
    dialog_analytics = DialogAnalytics.from_event(
        processor=processor,
        processed=processed,
        process_time=process_time,
        not_processed_reason=not_processed_reason,
        widget=input_,
        callback=None,
        message=message,
        manager=manager,
        aiogd_context_before=aiogd_context_before,
        aiogd_stack_before=aiogd_stack_before,
    )

    await dialog_analytics.save_to_clickhouse()
    logger.info(
        "User %s in chat %s input in %s %s in dialog %s (state %s)",
        dialog_analytics.user_id,
        dialog_analytics.telegram_chat_id,
        dialog_analytics.widget_type,
        dialog_analytics.widget_id,
        dialog_analytics.aiogd_context_intent_id,
        dialog_analytics.aiogd_context_state,
    )


async def message_input_process_message(
    self: MessageInput,
    message: Message,
    dialog: DialogProtocol,
    manager: DialogManager,
) -> bool:
    processed = True
    for handler_filter in self.filters:
        if not await handler_filter.call(
            manager.event,
            **manager.middleware_data,
        ):
            processed = False

    aiogd_context_before: Context = copy.deepcopy(manager.middleware_data[CONTEXT_KEY])
    aiogd_stack_before: Stack = copy.deepcopy(manager.middleware_data[STACK_KEY])

    if processed:
        start = time.perf_counter()
        await self.func.process_event(message, self, manager)
        process_time = time.perf_counter() - start
    else:
        process_time = None

    await save_input_statistics(
        processor="message_input_process_message",
        processed=processed,
        process_time=process_time,
        not_processed_reason=None if processed else "filtered",
        input_=self,
        message=message,
        manager=manager,
        aiogd_context_before=aiogd_context_before,
        aiogd_stack_before=aiogd_stack_before,
    )

    return True


async def text_input_process_message(
    self: TextInput,
    message: Message,
    dialog: DialogProtocol,
    manager: DialogManager,
) -> bool:
    aiogd_context_before: Context = copy.deepcopy(manager.middleware_data[CONTEXT_KEY])
    aiogd_stack_before: Stack = copy.deepcopy(manager.middleware_data[STACK_KEY])

    if message.content_type != ContentType.TEXT:
        await save_input_statistics(
            processor="text_input_process_message",
            processed=False,
            process_time=None,
            not_processed_reason="wrong content type",
            input_=self,
            message=message,
            manager=manager,
            aiogd_context_before=aiogd_context_before,
            aiogd_stack_before=aiogd_stack_before,
        )

        return False

    if self.filter and not await self.filter.call(
        manager.event,
        **manager.middleware_data,
    ):
        await save_input_statistics(
            processor="text_input_process_message",
            processed=False,
            process_time=None,
            not_processed_reason="filtered",
            input_=self,
            message=message,
            manager=manager,
            aiogd_context_before=aiogd_context_before,
            aiogd_stack_before=aiogd_stack_before,
        )
        return False
    start = time.perf_counter()
    try:
        value = self.type_factory(message.text)
    except ValueError as err:
        await self.on_error.process_event(
            message,
            self.managed(manager),
            manager,
            err,
        )
    else:
        # store original text
        self.set_widget_data(manager, message.text)
        await self.on_success.process_event(
            message,
            self.managed(manager),
            manager,
            value,
        )
    end = time.perf_counter()

    await save_input_statistics(
        processor="text_input_process_message",
        processed=True,
        process_time=end - start,
        not_processed_reason=None,
        input_=self,
        message=message,
        manager=manager,
        aiogd_context_before=aiogd_context_before,
        aiogd_stack_before=aiogd_stack_before,
    )

    return True


def patch_input():
    MessageInput.process_message = message_input_process_message
    TextInput.process_message = text_input_process_message


def setup_dialog_analytics():
    logger.debug("Ensuring clickhouse tables for dialog analytics")
    with open(DIALOG_ANALYTICS_DDL_SQL, encoding="utf-8") as sql_file:  # noqa: PTH123
        task = clickhouse.run_sql_from_sync(sql_file.read())
        task.add_done_callback(_pending_tasks.remove)
        _pending_tasks.add(task)

    patch_keyboard()
    patch_input()

    # Нужно для работы djgram.contrib.forms
    global DIALOG_ANALYTICS_ENABLED  # noqa: PLW0603
    DIALOG_ANALYTICS_ENABLED = True
