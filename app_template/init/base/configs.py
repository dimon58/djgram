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

#: Ссылка для подключения к базе данных
DB_URL = "sqlite+aiosqlite:///db.sqlite3"

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
