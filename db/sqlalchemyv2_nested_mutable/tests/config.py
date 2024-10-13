# ruff: noqa
# type: ignore
import os
import random
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

env_path = Path("./") / ".env"
load_dotenv(dotenv_path=env_path)


@lru_cache()
class Settings:
    POSTGRES_IMAGE_NAME: str = os.getenv("POSTGRES_IMAGE_NAME", "postgres:15")
    POSTGRES_CONTAINER_NAME: str = os.getenv("POSTGRES_CONTAINER_NAME", f"pytest-{random.randint(0, int(1e8))}")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "test")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "test")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "127.0.0.1")  # 172.17.0.1, host.docker.internal
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432/tcp")
    POSTGRES_FWD_PORT: str = os.getenv(
        "POSTGRES_FWD_PORT", "6000"
    )  # None ~ will result in a random port being assigned by vscode
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "test")
    POSTGRES_DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    POSTGRES_ECHO: bool = os.getenv("POSTGRES_ECHO", "True") == "True"


settings = Settings()
