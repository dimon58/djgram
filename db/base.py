from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from djgram.configs import DB_ENGINE_SETTINGS, DB_URL

db_engine = create_async_engine(
    url=DB_URL,
    **DB_ENGINE_SETTINGS,
)
async_session_maker = async_sessionmaker(bind=db_engine, autocommit=False, expire_on_commit=False)
