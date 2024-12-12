"""
Лимитёр запрос к bot api

Основан на https://github.com/chazovtema/limited_aiogram
и https://github.com/python-telegram-bot/python-telegram-bot/blob/master/telegram/ext/_aioratelimiter.py
"""

import asyncio
import logging
from collections.abc import Awaitable
from typing import Any, TypeAlias

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramRetryAfter
from aiogram.methods import SendMessage, TelegramMethod
from aiogram.methods.base import TelegramType
from cachetools import TTLCache
from limiter import Limiter

from djgram.system_configs import (
    LIMIT_CALLER_CHAT_LIMITER_CACHE_MAX_SIZE,
    LIMIT_CALLER_CHAT_LIMITER_CACHE_TTL_SECONDS,
    LIMIT_CALLER_GROUP_LIMITER_CACHE_MAX_SIZE,
    LIMIT_CALLER_GROUP_LIMITER_CACHE_TTL_SECONDS,
)

from .constants import MAX_MESSAGES_PER_GROUP_PER_SECOND, MAX_MESSAGES_PER_SECOND, MAX_MESSAGES_PER_USER_PER_SECOND

ChatIdType: TypeAlias = int | str

logger = logging.getLogger("limiter")


class LimitCaller:  # noqa: D101
    __slots__ = (
        "_overall_max_rate",
        "_user_max_rate",
        "_group_max_rate",
        "max_retries",
        "main_limiter",
        "chats_limiter",
        "groups_limiter",
    )

    def __init__(
        self,
        overall_max_rate: float = MAX_MESSAGES_PER_SECOND,
        user_max_rate: float = MAX_MESSAGES_PER_USER_PER_SECOND,
        group_max_rate: float = MAX_MESSAGES_PER_GROUP_PER_SECOND,
        max_retries: int = 0,
    ) -> None:
        """
        A class that controls the speed of sending requests.

        :param overall_max_rate: maximum messages per seconds in all chats in total
        :param user_max_rate: maximum messages per seconds for each user
        :param group_max_rate: maximum messages per seconds for each group
        :param max_retries: maximum retires on TelegramRetryAfter exception
        """

        self._overall_max_rate = overall_max_rate
        self._user_max_rate = user_max_rate
        self._group_max_rate = group_max_rate

        if max_retries < 0:
            raise ValueError("max_retries should be greater or equal 0")
        self.max_retries = max_retries

        self.main_limiter = Limiter(self._overall_max_rate)
        # 2**63 = no limit for cache size
        self.groups_limiter = TTLCache[ChatIdType, Limiter](
            maxsize=LIMIT_CALLER_GROUP_LIMITER_CACHE_MAX_SIZE,
            ttl=LIMIT_CALLER_GROUP_LIMITER_CACHE_TTL_SECONDS,
        )
        self.chats_limiter = TTLCache[ChatIdType, Limiter](
            maxsize=LIMIT_CALLER_CHAT_LIMITER_CACHE_MAX_SIZE,
            ttl=LIMIT_CALLER_CHAT_LIMITER_CACHE_TTL_SECONDS,
        )

    async def _call_with_limit(
        self,
        chat_id: ChatIdType,
        coro: Awaitable[TelegramType],
        storage: TTLCache[ChatIdType, Limiter],
        rate: float,
        burst: int,
    ) -> TelegramType:
        """
        Calls the api method

        :param chat_id: telegram chat id
        :param coro: method
        :param storage: chat or group storage
        :param rate: call rate for limiters
        :param burst: burst for limiters
        """

        async with self.main_limiter:
            limiter = storage.get(chat_id)
            if not limiter:
                limiter = Limiter(rate, burst)
                storage[chat_id] = limiter
                async with limiter:
                    return await coro
            else:
                async with limiter:
                    return await coro

    async def call(self, chat_id: ChatIdType, coro: Awaitable[TelegramType]) -> TelegramType:
        if isinstance(chat_id, str) or chat_id < 0:
            return await self._call_with_limit(chat_id, coro, self.groups_limiter, self._group_max_rate, 20)

        return await self._call_with_limit(chat_id, coro, self.chats_limiter, self._user_max_rate, 3)


class LimitedBot(Bot):
    """
    Бот с ограничением запросов в секунду к серверам телеграм
    """

    def __init__(
        self,
        token: str,
        limiter: LimitCaller,
        session: BaseSession | None = None,
        default: DefaultBotProperties | None = None,
        **kwargs: Any,
    ):
        """
        LimitedBot class

        :param token: Telegram Bot token `Obtained from @BotFather <https://t.me/BotFather>`_
        :param limiter: limiter instance
        :param session: HTTP Client session (For example AiohttpSession).
            If not specified it will be automatically created.
        :param default: Default bot properties.
            If specified it will be propagated into the API methods at runtime.
        :raise TokenValidationError: When token has invalid format this exception will be raised
        """

        super().__init__(token=token, session=session, default=default, **kwargs)

        self.caller = limiter
        self.__original__call__ = Bot.__call__

    async def _call(self, method: TelegramMethod[TelegramType], request_timeout: int | None = None) -> TelegramType:  # pyright: ignore [reportReturnType]
        """
        Just to not modify __init__ method
        """

        # initial call and max_retries
        for attempt in range(self.caller.max_retries + 1):  # noqa: RET503
            try:
                # In case a retry_after was hit, we wait with processing the request
                await self._retry_after_event.wait()

                # run request
                coro = self.__original__call__(  # pyright: ignore [reportCallIssue]
                    method=method,
                    request_timeout=request_timeout,
                )
                # if hasattr(method, "chat_id") and not isinstance(method, GetChat):
                if isinstance(method, SendMessage):
                    return await self.caller.call(method.chat_id, coro)  # pyright: ignore [reportReturnType]

                return await coro  # pyright: ignore [reportReturnType]

            except TelegramRetryAfter as exc:
                if attempt == self.caller.max_retries:
                    logger.exception(
                        "Rate limit hit after maximum of %d retries",
                        self.caller.max_retries,
                        exc_info=exc,
                    )
                    raise

                logger.info(exc)
                # Make sure we don't allow other requests to be processed
                self._retry_after_event.clear()
                await asyncio.sleep(exc.retry_after + 0.1)  # additional 0.1 sec gap
            finally:
                # Allow other requests to be processed
                self._retry_after_event.set()

    async def __call__(self, method: TelegramMethod[TelegramType], request_timeout: int | None = None) -> TelegramType:
        caller = getattr(self, "caller", None)
        if not caller:
            self.caller = LimitCaller()

        self.__call__ = LimitedBot._call  # pyright: ignore [reportAttributeAccessIssue]

        if not getattr(self, "_retry_after_event", None):
            # lock on TelegramRetryAfter exception
            self._retry_after_event = asyncio.Event()
            self._retry_after_event.set()

        return await LimitedBot._call(self, method, request_timeout)


def patch_bot_with_limiter() -> None:
    """
    Patches the bot, these changes are not reversible

    If you want to use non-default limiter setting use LimitedBot class instead of Bot
    """
    Bot.__original__call__ = Bot.__call__  # pyright: ignore [reportAttributeAccessIssue]
    Bot.__call__ = LimitedBot.__call__  # pyright: ignore [reportAttributeAccessIssue]
