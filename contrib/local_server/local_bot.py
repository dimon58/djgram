import re
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TypeVar

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.types import File

from djgram.utils.misc import unfreeze_model

T = TypeVar("T")


class SemiLocalBot(Bot):
    """
    Принудительно скачивает файлы по сети, даже при использовании локального сервера

    Стоит использовать вместе с nginx
    """

    _PATH_REGEX = re.compile(r"^/var/lib/telegram-bot-api/\d+:[\w-]+/(.+)$")

    async def get_file(
        self,
        file_id: str,
        request_timeout: int | None = None,
    ) -> File:
        file_ = await super().get_file(file_id, request_timeout)

        with unfreeze_model(file_):
            # /var/lib/telegram-bot-api/<token>/<path>
            # noinspection Pydantic
            file_.file_path = re.match(self._PATH_REGEX, file_.file_path).group(1)

        return file_


def get_local_bot(
    telegram_bot_token: str,
    telegram_local: bool,
    telegram_local_server_url: str,
    telegram_local_server_files_url: str,
) -> Bot:
    if telegram_local:
        # Читает файлы напрямую с диска. Будет работать, только если запускать сервер и бота в одном контейнере
        bot_class = Bot
        api_server = TelegramAPIServer.from_base(telegram_local_server_url, is_local=True)
    else:
        # Читает файлы по сети. Можно использовать вместе с nginx для удобства.
        bot_class = SemiLocalBot
        method_base = telegram_local_server_url.rstrip("/")
        file_base = telegram_local_server_files_url.rstrip("/")
        api_server = TelegramAPIServer(
            base=f"{method_base}/bot{{token}}/{{method}}",
            file=f"{file_base}/file/bot{{token}}/{{path}}",
            is_local=False,
        )

    session = AiohttpSession(api=api_server)

    return bot_class(telegram_bot_token, session=session)


@asynccontextmanager
async def get_local_bot_context(
    telegram_bot_token: str,
    telegram_local: bool,
    telegram_local_server_url: str,
    telegram_local_server_files_url: str,
) -> AbstractAsyncContextManager[Bot]:
    bot = get_local_bot(
        telegram_bot_token=telegram_bot_token,
        telegram_local=telegram_local,
        telegram_local_server_url=telegram_local_server_url,
        telegram_local_server_files_url=telegram_local_server_files_url,
    )
    try:
        yield bot
    finally:
        await bot.session.close()
