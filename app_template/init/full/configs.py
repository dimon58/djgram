import os
from pathlib import Path

from dotenv import load_dotenv

#: Корень проекта
BASE_DIR = Path(__file__).resolve().parent

# Переменные окружения из файла .env
# Загружаем без перезаписи, чтобы ими можно было управлять из вне
load_dotenv(BASE_DIR / ".env", override=False)

#: Включить режим отладки
DEBUG = bool(int(os.environ.get("DEBUG", "1")))  # pyright: ignore [reportArgumentType]

# --------------------------------- api токены --------------------------------- #

#: Токен телеграм бота
TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")  # pyright: ignore [reportAssignmentType]

# ---------- База данных ---------- #

# Данные для подключения к PostgreSQL
POSTGRES_HOST: str = os.environ.get("POSTGRES_HOST", "localhost")  # pyright: ignore [reportAssignmentType]
POSTGRES_PORT: int = int(os.environ.get("POSTGRES_PORT", "5432"))  # pyright: ignore [reportArgumentType]
POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "postgres")  # pyright: ignore [reportAssignmentType]
POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "admin")  # pyright: ignore [reportAssignmentType]
POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "admin")  # pyright: ignore [reportAssignmentType]

# https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
DB_URL = "postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}".format(  # noqa: UP032
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    dbname=POSTGRES_DB,
)

DB_ENGINE_SETTINGS = {
    # https://stackoverflow.com/questions/24956894/sql-alchemy-queuepool-limit-overflow
    "pool_size": 25,
}
DB_SUPPORTS_ARRAYS = True

# Данные для подключения к ClickHouse
CLICKHOUSE_HOST: str = os.environ.get("CLICKHOUSE_HOST", "localhost")  # pyright: ignore [reportAssignmentType]
CLICKHOUSE_PORT: int = int(os.environ.get("CLICKHOUSE_PORT", 9000))  # pyright: ignore [reportArgumentType]
CLICKHOUSE_DB: str = os.environ.get("CLICKHOUSE_DB", "default")  # pyright: ignore [reportAssignmentType]
CLICKHOUSE_USER: str = os.environ.get("CLICKHOUSE_USER", "default")  # pyright: ignore [reportAssignmentType]
CLICKHOUSE_PASSWORD: str = os.environ.get("CLICKHOUSE_PASSWORD", "")  # pyright: ignore [reportAssignmentType]

REDIS_HOST: str = os.environ.get("REDIS_HOST", "localhost")  # pyright: ignore [reportAssignmentType]
REDIS_PORT: int = int(os.environ.get("REDIS_PORT", 6379))  # pyright: ignore [reportArgumentType]
REDIS_USER: str | None = os.environ.get("REDIS_USER")
REDIS_PASSWORD: str | None = os.environ.get("REDIS_PASSWORD")

#: Номер базы данных для хранилища машины конченых состояний
REDIS_STORAGE_DB: int = int(os.environ.get("REDIS_STORAGE_DB", 0))  # pyright: ignore [reportArgumentType]

# ---------- Логирование ---------- #

#: Папка для логирования
LOGGING_FOLDER = BASE_DIR / "logs"
LOGGING_FOLDER.mkdir(exist_ok=True)

#: Файл с логами
LOG_FILE = LOGGING_FOLDER / "logs.log"

#: Формат логов
# Красим точку в тот же цвет, что и дату и миллисекунды
LOGGING_FORMAT = (
    "[%(name)s:%(filename)s:%(funcName)s:%(lineno)d:"
    "%(asctime)s\033[32m.\033[0m%(msecs)03d:%(levelname)s:%(update_id)s] %(message)s"
)

#: Формат даты в логах
LOGGING_DATE_FORMAT = "%d-%m-%Y %H:%M:%S"

#: Настройки логирования
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "update_filter": {
            "()": "djgram.contrib.logs.context.UpdateIdContextFilter",
        },
    },
    "formatters": {
        "default": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": LOGGING_FORMAT,
            "datefmt": LOGGING_DATE_FORMAT,
        },
        "colored": {
            "()": "djgram.contrib.logs.extended_colored_formatter.ExtendedColoredFormatter",
            "format": LOGGING_FORMAT,
            "datefmt": LOGGING_DATE_FORMAT,
            "field_styles": {
                "asctime": {"color": "green"},
                "hostname": {"color": "magenta"},
                "name": {"color": "blue"},
                "programname": {"color": "cyan"},
                "username": {"color": "yellow"},
            },
        },
    },
    "handlers": {
        "stream_handler": {
            "class": "logging.StreamHandler",
            "formatter": "colored",
            "filters": ["update_filter"],
        },
        "file_handler": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "default",
            "filters": ["update_filter"],
            "filename": LOG_FILE,
            "encoding": "utf-8",
            "when": "W0",
        },
    },
    "loggers": {
        "root": {
            "handlers": ["stream_handler", "file_handler"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
            "encoding": "utf-8",
        },
        "sqlalchemy.engine": {
            "level": "DEBUG" if DEBUG else "WARNING",
        },
    },
}
