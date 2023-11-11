from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import configs

db_engine = create_async_engine(
    url=configs.DB_URL,
    pool_size=configs.DB_ENGINE_POOL_SIZE,
)
async_session_maker = async_sessionmaker(bind=db_engine, autocommit=False, expire_on_commit=False)
