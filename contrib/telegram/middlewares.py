"""
Посредники для сохранения пользователей в базу
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

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

    async def save_telegram_user_to_db(self, user: User, db_session: AsyncSession) -> tuple[TelegramUser, bool]:
        """
        Сохраняет пользователя в базе
        """
        telegram_user, telegram_user_state = await insert_or_update(
            session=db_session,
            model=TelegramUser,
            keys={"id": user.id},
            other_attr={field: getattr(user, field) for field in self.__telegram_user_fields},
        )

        if telegram_user_state == ReturnState.CREATED:
            logger.info("New Telegram user [%s] %s", telegram_user.id, user.full_name)

        return telegram_user, telegram_user_state == ReturnState.CREATED

    async def save_telegram_chat_to_db(self, chat: Chat, db_session: AsyncSession) -> tuple[TelegramChat, bool]:
        """
        Сохраняет чат в базе
        """
        telegram_chat, telegram_chat_state = await insert_or_update(
            session=db_session,
            model=TelegramChat,
            keys={"id": chat.id},
            other_attr={field: getattr(chat, field) for field in self.__telegram_chat_fields},
        )

        if telegram_chat_state == ReturnState.CREATED:
            logger.info("New Telegram %s chat [%s]", chat.type, chat.id)

        return telegram_chat, telegram_chat_state == ReturnState.CREATED

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

        telegram_user_created = telegram_chat_created = False

        if telegram_user is not None:
            data[MIDDLEWARE_TELEGRAM_USER_KEY], telegram_user_created = await self.save_telegram_user_to_db(
                telegram_user, db_session
            )
        if telegram_chat is not None:
            data[MIDDLEWARE_TELEGRAM_CHAT_KEY], telegram_chat_created = await self.save_telegram_chat_to_db(
                telegram_chat, db_session
            )

        if telegram_user_created or telegram_chat_created:
            await db_session.commit()
            await db_session.begin()

        return await handler(update, data)
