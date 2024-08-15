"""
Посредники для сохранения пользователей в базу
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from aiogram import BaseMiddleware
from aiogram.types import Chat, ChatBoostRemoved, ChatBoostUpdated, Update, User
from sqlalchemy.ext.asyncio import AsyncSession

from djgram.contrib.telegram.models import TelegramChat, TelegramUser
from djgram.db.middlewares import MIDDLEWARE_DB_SESSION_KEY
from djgram.db.models import BaseModel, CreatedAtMixin, UpdatedAtMixin
from djgram.db.utils import (
    ReturnState,
    get_fields_of_declarative_meta,
    insert_or_update,
)

T = TypeVar("T", bound=BaseModel)

MIDDLEWARE_TELEGRAM_USER_KEY = "telegram_user"
MIDDLEWARE_TELEGRAM_CHAT_KEY = "telegram_chat"

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class TelegramMiddleware(BaseMiddleware):
    """
    Посредник для сохранения пользователя и чата telegram в базу данных
    в аргументы telegram_user и telegram_chat соответственно

    Требует подключенной ранее DbSessionMiddleware
    """

    __base_model_fields: set[str] = (
        get_fields_of_declarative_meta(BaseModel)
        | get_fields_of_declarative_meta(CreatedAtMixin)
        | get_fields_of_declarative_meta(UpdatedAtMixin)
    )
    __telegram_user_fields = set(TelegramUser.__table__.columns.keys()) - __base_model_fields
    __telegram_chat_fields = set(TelegramChat.__table__.columns.keys()) - __base_model_fields

    @staticmethod
    async def save_to_db(
        obj: User | Chat, model: type[T], exclude_fields: set[str], db_session: AsyncSession, id_field: str
    ) -> tuple[T, ReturnState]:
        return await insert_or_update(
            session=db_session,
            model=model,
            keys={id_field: obj.id},
            other_attr={field: getattr(obj, field) for field in exclude_fields},
        )

    @staticmethod
    def log_state(result: tuple[TelegramUser | TelegramChat, ReturnState]) -> None:
        obj, return_state = result

        if return_state == ReturnState.CREATED:
            logger.info("New %s", obj)
        elif return_state == ReturnState.UPDATED:
            logger.info("Updated %s", obj)
        elif return_state == ReturnState.NOT_MODIFIED:
            logger.debug("Not modified %s", obj)
        else:
            logger.warning("Not implemented logging state %s for %s", return_state, obj)

    async def save_telegram_user_to_db(self, user: User, db_session: AsyncSession) -> tuple[TelegramUser, ReturnState]:
        """
        Сохраняет пользователя в базе
        """

        result = await self.save_to_db(
            obj=user,
            model=TelegramUser,
            exclude_fields=self.__telegram_user_fields,
            db_session=db_session,
            id_field="id",
        )

        self.log_state(result)

        return result

    async def save_telegram_chat_to_db(self, chat: Chat, db_session: AsyncSession) -> tuple[TelegramChat, ReturnState]:
        """
        Сохраняет чат в базе
        """

        result = await self.save_to_db(
            obj=chat,
            model=TelegramChat,
            exclude_fields=self.__telegram_chat_fields,
            db_session=db_session,
            id_field="id",
        )

        self.log_state(result)

        return result

    @staticmethod
    def get_telegram_user_and_chat(update: Update) -> tuple[User | None, Chat | None]:
        r"""
        Возвращает пользователя и чат telegram


        В таблице указаны расположения пользователя и чата в объекте события

        \* значит, что нет полноценного поля, но есть его части

        +-----------------------------+-----------------------------+----------------------+
        | Тип события                 | Путь до пользователя        | Путь до чата         |
        +=============================+=============================+======================+
        | BusinessConnection          | user                        | *user_chat_id        |
        +-----------------------------+-----------------------------+----------------------+
        | BusinessMessagesDeleted     |                             | chat                 |
        +-----------------------------+-----------------------------+----------------------+
        | CallbackQuery               | from_user                   | message.chat         |
        +-----------------------------+-----------------------------+----------------------+
        | ChatBoostRemoved            | Optional[boost.source.user] |                      |
        +-----------------------------+-----------------------------+----------------------+
        | ChatBoostUpdated            | Optional[boost.source.user] | chat                 |
        +-----------------------------+-----------------------------+----------------------+
        | ChatJoinRequest             | from_user                   | chat                 |
        +-----------------------------+-----------------------------+----------------------+
        | ChatMemberUpdated           | from_user                   | chat                 |
        +-----------------------------+-----------------------------+----------------------+
        | ChosenInlineResult          | from_user                   |                      |
        +-----------------------------+-----------------------------+----------------------+
        | InlineQuery                 | from_user                   | *chat_type           |
        +-----------------------------+-----------------------------+----------------------+
        | Message                     | from_user                   | chat                 |
        +-----------------------------+-----------------------------+----------------------+
        | MessageReactionCountUpdated |                             | chat                 |
        +-----------------------------+-----------------------------+----------------------+
        | MessageReactionUpdated      | user                        | chat or *actor_chat  |
        +-----------------------------+-----------------------------+----------------------+
        | Poll                        |                             |                      |
        +-----------------------------+-----------------------------+----------------------+
        | PollAnswer                  | Optional[user]              |                      |
        +-----------------------------+-----------------------------+----------------------+
        | PreCheckoutQuery            | from_user                   |                      |
        +-----------------------------+-----------------------------+----------------------+
        | ShippingQuery               | from_user                   |                      |
        +-----------------------------+-----------------------------+----------------------+
        """

        event = update.event

        # CallbackQuery
        # ChatJoinRequest
        # ChatMemberUpdated
        # ChosenInlineResult
        # InlineQuery
        # Message
        # PreCheckoutQuery
        # ShippingQuery
        user = getattr(event, "from_user", None)
        if user is None:
            # BusinessConnection
            # MessageReactionUpdated
            # PollAnswer
            user = getattr(event, "user", None)
        # ChatBoostRemoved
        # ChatBoostUpdated
        if user is None and isinstance(event, ChatBoostRemoved | ChatBoostUpdated):
            user = event.boost.source.user

        # BusinessMessagesDeleted
        # ChatBoostUpdated
        # ChatJoinRequest
        # ChatMemberUpdated
        # Message
        # MessageReactionCountUpdated
        # MessageReactionUpdated
        chat = getattr(event, "chat", None)
        if chat is None and (message := getattr(event, "message", None)) is not None:
            # CallbackQuery
            chat = message.chat

        return user, chat

    async def __call__(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:
        db_session: AsyncSession | None = data.get(MIDDLEWARE_DB_SESSION_KEY)
        if db_session is None:
            raise ValueError(f"You should install DbSessionMiddleware to use {self.__class__.__name__}")

        telegram_user, telegram_chat = self.get_telegram_user_and_chat(update)

        need_commit = False

        if telegram_user is not None:
            data[MIDDLEWARE_TELEGRAM_USER_KEY], telegram_user_return_state = await self.save_telegram_user_to_db(
                telegram_user, db_session
            )
            need_commit = need_commit or telegram_user_return_state.need_commit()

        if telegram_chat is not None:
            data[MIDDLEWARE_TELEGRAM_CHAT_KEY], telegram_chat_return_state = await self.save_telegram_chat_to_db(
                telegram_chat, db_session
            )
            need_commit = need_commit or telegram_chat_return_state.need_commit()

        if need_commit:
            await db_session.commit()
            await db_session.begin()

        return await handler(update, data)
