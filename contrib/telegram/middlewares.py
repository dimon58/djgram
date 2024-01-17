"""
Посредники для сохранения пользователей в базу
"""
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Chat, Update, User
from sqlalchemy.ext.asyncio import AsyncSession

from djgram.contrib.telegram.models import TelegramChat, TelegramUser
from djgram.db.models import BaseModel
from djgram.db.utils import (
    ReturnState,
    get_fields_of_declarative_meta,
    insert_or_update,
)

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class TelegramMiddleware(BaseMiddleware):
    """
    Посредник для сохранения пользователя и чата telegram в базу данных
    в аргументы telegram_user и telegram_chat соответственно

    Требует подключенной ранее DbSessionMiddleware
    """

    CHAT_EXCLUDED_FIELDS = {
        "has_aggressive_anti_spam_enabled",
        "photo_id",
        "location_id",
        "has_hidden_members",
        "permissions_id",
    }

    __base_model_fields = get_fields_of_declarative_meta(BaseModel) | {"created_at", "updated_at"}
    __telegram_user_fields = set(TelegramUser.__table__.columns.keys()) - __base_model_fields
    __telegram_chat_fields = set(TelegramChat.__table__.columns.keys()) - __base_model_fields - CHAT_EXCLUDED_FIELDS

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
            logger.info(f"New Telegram user [{telegram_user.id}] {user.full_name}")

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
            logger.info(f"New Telegram chat [{chat.id}]")

        return telegram_chat, telegram_chat_state == ReturnState.CREATED

    @staticmethod
    def get_user_and_chat(update: Update) -> tuple[User | None, Chat | None]:
        """
        Возвращает пользователя и чат telegram
        """

        event = update.event

        user = getattr(event, "from_user", None)
        chat = getattr(event, "chat", None)

        if chat is None and (message := getattr(event, "message", None)) is not None:
            chat = message.chat

        return user, chat

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:
        db_session: AsyncSession | None = data.get("db_session")
        if db_session is None:
            raise ValueError(f"You should install DbSessionMiddleware to use {self.__class__.__name__}")

        user, chat = self.get_user_and_chat(update)

        telegram_user_created = telegram_chat_created = False

        if user is not None:
            data["telegram_user"], telegram_user_created = await self.save_telegram_user_to_db(user, db_session)
        if chat is not None:
            data["telegram_chat"], telegram_chat_created = await self.save_telegram_chat_to_db(chat, db_session)

        if telegram_user_created or telegram_chat_created:
            await db_session.commit()
            await db_session.begin()

        return await handler(update, data)
