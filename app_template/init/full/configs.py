from pathlib import Path

from dotenv import dotenv_values

#: Корень проекта
BASE_DIR = Path(__file__).resolve().parent

#: Переменные окружения из файла .env
env = dotenv_values(BASE_DIR / ".env")

#: Включить режим отладки
DEBUG = bool(int(env.get("DEBUG", "1")))  # pyright: ignore [reportArgumentType]

# --------------------------------- api токены --------------------------------- #

#: Токен телеграм бота
TELEGRAM_BOT_TOKEN: str = env.get("TELEGRAM_BOT_TOKEN", "")  # pyright: ignore [reportAssignmentType]

# ---------- База данных ---------- #

# Данные для подключения к PostgreSQL
POSTGRES_HOST: str = env.get("POSTGRES_HOST", "localhost")  # pyright: ignore [reportAssignmentType]
POSTGRES_PORT: int = int(env.get("POSTGRES_PORT", "5432"))  # pyright: ignore [reportArgumentType]
POSTGRES_DB: str = env.get("POSTGRES_DB", "local")  # pyright: ignore [reportAssignmentType]
POSTGRES_USER: str = env.get("POSTGRES_USER", "admin")  # pyright: ignore [reportAssignmentType]
POSTGRES_PASSWORD: str = env.get("POSTGRES_PASSWORD", "admin")  # pyright: ignore [reportAssignmentType]

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
CLICKHOUSE_HOST: str = env.get("CLICKHOUSE_HOST", "localhost")  # pyright: ignore [reportAssignmentType]
CLICKHOUSE_PORT: int = int(env.get("CLICKHOUSE_PORT", 9000))  # pyright: ignore [reportArgumentType]
CLICKHOUSE_DB: str = env.get("CLICKHOUSE_DB", "default")  # pyright: ignore [reportAssignmentType]
CLICKHOUSE_USER: str = env.get("CLICKHOUSE_USER", "default")  # pyright: ignore [reportAssignmentType]
CLICKHOUSE_PASSWORD: str = env.get("CLICKHOUSE_PASSWORD", "password")  # pyright: ignore [reportAssignmentType]

#: Redis host
REDIS_HOST: str = env.get("REDIS_HOST", "localhost")  # pyright: ignore [reportAssignmentType]
#: Redis port
REDIS_PORT: int = int(env.get("REDIS_PORT", 6379))  # pyright: ignore [reportArgumentType]

#: Номер базы данных для хранилища машины конченых состояний
REDIS_STORAGE_DB: int = int(env.get("REDIS_STORAGE_DB", 0))  # pyright: ignore [reportArgumentType]

# ---------- Логирование ---------- #

#: Папка для логирования
LOGGING_FOLDER = BASE_DIR / "logs"
LOGGING_FOLDER.mkdir(exist_ok=True)

#: Файл с логами
LOG_FILE = LOGGING_FOLDER / "logs.log"

#: Формат логов
LOGGING_FORMAT = "[%(name)s:%(filename)s:%(funcName)s:%(lineno)d:%(asctime)s:%(levelname)s] %(message)s"

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
            "class": "logging.FileHandler",
            "formatter": "default",
            "filters": ["update_filter"],
            "filename": LOG_FILE,
            "encoding": "utf-8",
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
