from asyncio import current_task
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)

from djgram.configs import DB_ENGINE_SETTINGS, DB_URL

db_engine = create_async_engine(
    url=DB_URL,
    **DB_ENGINE_SETTINGS,
)
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=db_engine,
    autocommit=False,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_async_scoped_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Функция получения сессии для работы с celery

    https://habr.com/ru/articles/721186/
    https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncio-scoped-session
    """
    scoped_factory = async_scoped_session(
        async_session_maker,
        scopefunc=current_task,
    )
    try:
        async with scoped_factory() as db_session:
            await db_session.begin()
            yield db_session
    finally:
        await scoped_factory.remove()
