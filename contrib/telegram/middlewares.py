"""
Посредники для сохранения пользователей в базу
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.middlewares.user_context import EventContext, UserContextMiddleware
from aiogram.types import Chat, ChatFullInfo, Update, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from djgram.configs import TELEGRAM_CHAT_FULL_INFO_UPDATE_ON_EACH_EVENT, TELEGRAM_CHAT_FULL_INFO_UPDATE_PERIOD
from djgram.contrib.telegram.models import TelegramChat, TelegramChatFullInfo, TelegramUser
from djgram.db.models import BaseModel, CreatedAtMixin, UpdatedAtMixin
from djgram.db.utils import ReturnState, get_fields_of_declarative_meta, insert_or_update
from djgram.system_configs import (
    MIDDLEWARE_DB_SESSION_KEY,
    MIDDLEWARE_TELEGRAM_BUSINESS_CONNECTION_ID_KEY,
    MIDDLEWARE_TELEGRAM_CHAT_FULL_INFO_KEY,
    MIDDLEWARE_TELEGRAM_CHAT_KEY,
    MIDDLEWARE_TELEGRAM_EVENT_CONTEXT_KEY,
    MIDDLEWARE_TELEGRAM_THREAD_ID_KEY,
    MIDDLEWARE_TELEGRAM_USER_KEY,
)

T = TypeVar("T", bound=BaseModel)

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
    __telegram_chat_full_info_fields = set(TelegramChatFullInfo.__table__.columns.keys()) - __base_model_fields

    @staticmethod
    async def save_to_db(
        obj: User | Chat | ChatFullInfo,
        model: type[T],
        exclude_fields: set[str],
        db_session: AsyncSession,
        id_field: str,
    ) -> tuple[T, ReturnState]:
        return await insert_or_update(
            session=db_session,
            model=model,
            keys={id_field: obj.id},
            other_attr={field: getattr(obj, field) for field in exclude_fields},
        )

    @staticmethod
    def log_state(result: tuple[TelegramUser | TelegramChat | TelegramChatFullInfo, ReturnState]) -> None:
        obj, return_state = result

        if return_state == ReturnState.CREATED:
            logger.info("New %s", obj.str_for_logging())
        elif return_state == ReturnState.UPDATED:
            logger.info("Updated %s", obj.str_for_logging())
        elif return_state == ReturnState.NOT_MODIFIED:
            logger.debug("Not modified %s", obj.str_for_logging())
        else:
            logger.warning("Not implemented logging state %s for %s", return_state, obj.str_for_logging())

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

    async def save_telegram_chat_full_info_to_db(
        self, chat_full_info: ChatFullInfo, db_session: AsyncSession
    ) -> tuple[TelegramChatFullInfo, ReturnState]:
        """
        Сохраняет полную информацию о чате в базе
        """

        update_fields = {field: getattr(chat_full_info, field) for field in self.__telegram_chat_full_info_fields}
        # Явно приписываем время обновления, чтобы гарантированно сохранить
        # в базе данных время последнего запроса данных из bot api
        update_fields["updated_at"] = datetime.now(tz=UTC)
        result = await insert_or_update(
            session=db_session,
            model=TelegramChatFullInfo,
            keys={"id": chat_full_info.id},
            other_attr=update_fields,
        )

        self.log_state(result)

        return result

    async def update_telegram_chat_full_info(
        self,
        data: dict[str, Any],
        db_session: AsyncSession,
        telegram_chat: Chat,
        bot: Bot,
    ) -> None:
        """
        Сохраняет обновленную полную информацию о чате в базе данных и данных для обработчика
        """
        logger.info("Updating chat full info %s", telegram_chat.id)

        telegram_chat_full_info = await bot.get_chat(telegram_chat.id)

        data[MIDDLEWARE_TELEGRAM_CHAT_FULL_INFO_KEY], telegram_chat_full_info_return_state = (
            await self.save_telegram_chat_full_info_to_db(telegram_chat_full_info, db_session)
        )

    async def __call__(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:
        db_session: AsyncSession | None = data.get(MIDDLEWARE_DB_SESSION_KEY)
        if db_session is None:
            raise ValueError(f"You should install DbSessionMiddleware to use {self.__class__.__name__}")

        event_context: EventContext = UserContextMiddleware.resolve_event_context(update)
        data[MIDDLEWARE_TELEGRAM_EVENT_CONTEXT_KEY] = event_context
        if event_context.thread_id is not None:
            data[MIDDLEWARE_TELEGRAM_THREAD_ID_KEY] = event_context.thread_id
        if event_context.business_connection_id is not None:
            data[MIDDLEWARE_TELEGRAM_BUSINESS_CONNECTION_ID_KEY] = event_context.business_connection_id
        telegram_user = event_context.user
        telegram_chat = event_context.chat

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
            telegram_chat_need_commit = telegram_chat_return_state.need_commit()
            need_commit = need_commit or telegram_chat_need_commit

            # TODO: Возможно стоит вынести задачу получения полной информации в фон,
            #  так она занимает несколько сотен миллисекунд,
            #  хотя вызывается достаточно редко
            # Чат изменился, значит обновляем и полную информацию
            # Или включено обновление каждый раз
            if telegram_chat_need_commit or TELEGRAM_CHAT_FULL_INFO_UPDATE_ON_EACH_EVENT:
                await self.update_telegram_chat_full_info(
                    data, db_session, telegram_chat, update.bot  # pyright: ignore [reportArgumentType]
                )
            else:
                chat_full_info_stmt = select(TelegramChatFullInfo).where(TelegramChatFullInfo.id == telegram_chat.id)
                telegram_chat_full_info: TelegramChatFullInfo | None = await db_session.scalar(chat_full_info_stmt)
                if telegram_chat_full_info is None:
                    logger.warning("There was no telegram chat full info %s in the database", telegram_chat.id)

                # Если по какой-то причине полной информации о чате не было или информация считалась устаревшей
                if (
                    telegram_chat_full_info is None
                    or datetime.now(tz=UTC) > telegram_chat_full_info.updated_at.astimezone(tz=UTC) + TELEGRAM_CHAT_FULL_INFO_UPDATE_PERIOD
                ):
                    await self.update_telegram_chat_full_info(
                        data, db_session, telegram_chat, update.bot  # pyright: ignore [reportArgumentType]
                    )
                else:
                    data[MIDDLEWARE_TELEGRAM_CHAT_FULL_INFO_KEY] = telegram_chat_full_info

        assert (MIDDLEWARE_TELEGRAM_CHAT_KEY in data) == (MIDDLEWARE_TELEGRAM_CHAT_FULL_INFO_KEY in data)  # noqa: S101

        if need_commit:
            await db_session.commit()
            await db_session.begin()

        return await handler(update, data)
