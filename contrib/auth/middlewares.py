"""
Посредники для аутентификации
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.enums import ChatType
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession

from djgram.configs import (
    BAN_MESSAGE,
    ENABLE_ACCESS_FOR_BANNED_ADMINS,
    ENABLE_BAN_MESSAGE,
)
from djgram.contrib.telegram.models import TelegramUser
from djgram.db.utils import get_or_create
from djgram.system_configs import (
    MIDDLEWARE_AUTH_USER_KEY,
    MIDDLEWARE_DB_SESSION_KEY,
    MIDDLEWARE_TELEGRAM_CHAT_KEY,
    MIDDLEWARE_TELEGRAM_USER_KEY,
)

from .models import User
from .user_model_base import AbstractUser

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class AuthMiddleware(BaseMiddleware):
    """
    Базовый функционал посредника для авторизации

    Добавляет поле user в data, которое является представлением записи о пользователе в базе данных

    Для работы требует TelegramMiddleware и DbSessionMiddleware
    """

    async def on_user_created(self, user: AbstractUser, db_session: AsyncSession) -> None:
        pass

    async def get_user(
        self,
        telegram_user: TelegramUser,
        db_session: AsyncSession,
    ) -> AbstractUser:
        user, user_created = await get_or_create(
            session=db_session,
            model=User,
            telegram_user_id=telegram_user.id,
        )

        if user_created:
            await db_session.commit()
            await db_session.begin()
            logger.info("New user [%s]", user.id)
            await self.on_user_created(user, db_session)

        user.last_interaction = datetime.now(tz=UTC)

        return user

    async def add_user_to_data(self, telegram_user: TelegramUser, data: dict[str, Any]) -> AbstractUser:
        """
        Добавляет пользователя в data
        """

        db_session = data.get(MIDDLEWARE_DB_SESSION_KEY)
        if db_session is None:
            raise ValueError(f"You should install DbSessionMiddleware to use {self.__class__.__name__}")

        user = await self.get_user(telegram_user, db_session)
        data[MIDDLEWARE_AUTH_USER_KEY] = user
        return user

    async def __call__(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:

        chat = data.get(MIDDLEWARE_TELEGRAM_CHAT_KEY)

        if chat is not None and chat.type == ChatType.CHANNEL:
            return await handler(update, data)

        telegram_user = data.get(MIDDLEWARE_TELEGRAM_USER_KEY)
        if telegram_user is None:
            raise ValueError(f"You should install TelegramMiddleware to use {self.__class__.__name__}")

        user = await self.add_user_to_data(telegram_user, data)

        # Если единственный админ забанит сам себя, то будет плохо
        if user.banned and not (ENABLE_ACCESS_FOR_BANNED_ADMINS and user.is_admin):
            if ENABLE_BAN_MESSAGE and chat is not None and chat.type == ChatType.PRIVATE:
                bot: Bot = data["bot"]
                await bot.send_message(
                    chat_id=chat.id,
                    text=BAN_MESSAGE,
                )
            logger.info("Skipped update %s from user %s due banned", update.update_id, user.id)
            return None

        return await handler(update, data)
