"""
Посредники для аутентификации
"""

import logging
from abc import ABC
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
from djgram.contrib.telegram.middlewares import MIDDLEWARE_TELEGRAM_CHAT_KEY
from djgram.contrib.telegram.models import TelegramUser
from djgram.db.utils import get_or_create

from .models import User
from .user_model_base import AbstractUser

MIDDLEWARE_USER_KEY = "user"

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class AuthMiddleware(BaseMiddleware, ABC):
    """
    Базовый функционал посредника для авторизации

    Добавляет поле user в data, которое является представлением записи о пользователе в базе данных

    Для работы требует TelegramMiddleware и DbSessionMiddleware
    """

    async def on_user_created(self, user: AbstractUser, db_session: AsyncSession):
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

        db_session = data.get("db_session")
        if db_session is None:
            raise ValueError(f"You should install DbSessionMiddleware to use {self.__class__.__name__}")

        user = await self.get_user(telegram_user, db_session)
        data[MIDDLEWARE_USER_KEY] = user
        return user

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:

        chat = data.get(MIDDLEWARE_TELEGRAM_CHAT_KEY)

        if chat is not None and chat.type == ChatType.CHANNEL:
            return await handler(update, data)

        user = data.get(MIDDLEWARE_TELEGRAM_CHAT_KEY)
        if user is None:
            raise ValueError(f"You should install TelegramMiddleware to use {self.__class__.__name__}")

        user = await self.add_user_to_data(user, data)

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
