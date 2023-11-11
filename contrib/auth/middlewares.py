"""
Посредники для аутентификации
"""
import logging
from abc import ABC
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession

from djgram.db.utils import get_or_create

from ..telegram.models import TelegramUser
from .models import User

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class AuthMiddleware(BaseMiddleware, ABC):
    """
    Базовый функционал посредника для авторизации

    Добавляет поле user в data, которое является представлением записи о пользователе в базе данных

    Для работы требует TelegramMiddleware и DbSessionMiddleware
    """

    @staticmethod
    async def get_user(telegram_user: TelegramUser, db_session: AsyncSession):
        user, user_created = await get_or_create(
            session=db_session,
            model=User,
            telegram_user_id=telegram_user.id,
        )

        if user_created:
            logger.info(f"New user [{user.id}]")

        user.last_interaction = datetime.now(tz=UTC)

        return user

    async def add_user_to_data(self, telegram_user: TelegramUser, data: dict[str, Any]):
        """
        Добавляет пользователя в data
        """

        db_session = data.get("db_session")
        if db_session is None:
            raise ValueError(f"You should install DbSessionMiddleware to use {self.__class__.__name__}")

        data["user"] = await self.get_user(telegram_user, db_session)

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("telegram_user")
        if user is None:
            raise ValueError(f"You should install TelegramMiddleware to use {self.__class__.__name__}")

        await self.add_user_to_data(user, data)
        return await handler(update, data)
