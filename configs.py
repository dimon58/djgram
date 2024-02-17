from contextlib import suppress

MEDIA_DIR = None

# Настройки базы данных
DB_URL = "sqlite+aiosqlite:///db.sqlite3"
DB_ENGINE_SETTINGS = {}
DB_METADATA = None
DB_SUPPORTS_ARRAYS = False

# Настройки clickhouse
CLICKHOUSE_HOST: str = "localhost"
CLICKHOUSE_PORT: int = 9000
CLICKHOUSE_DB: str = "default"
CLICKHOUSE_USER: str = "default"
CLICKHOUSE_PASSWORD: str = ""

#: Таблица в clickhouse, в которую логируются все обновления телеграмм
#   https://core.telegram.org/bots/api#getting-updates
ANALYTICS_UPDATES_TABLE = "update"
#: Таблица в clickhouse, в которую сохраняется общая статистика локального сервера
ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_GENERAL_TABLE = "general_statistics"
#: Таблица в clickhouse, в которую сохраняется статистика по каждому боту, подключенному к локальному серверу
ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_BOT_TABLE = "bot_statistics"
#: Период сбора статистики локального сервера в секундах
ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_COLLECTION_PERIOD = 60
#: Какое среднее сохраняется в статистику, возможные варианты
# 1 - inf, 2 - 5 sec, 3 - 1 min, 4 - 1 hour
ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_AVERAGE_INDEX = 3

#: Путь до папки с диаграммами диалогов
DIALOG_DIAGRAMS_DIR = "dialog_diagrams"

#: Включить генерацию диаграмм диалогов aiogram-dialogs
ENABLE_DIALOG_DIAGRAMS_GENERATION = True

#: Какое время пользователь считает активным для получения рассылки
ACTIVE_USER_TIMEOUT = 60 * 60 * 24 * 14

TELEGRAM_BROADCAST_TIMEOUT = 0.05  # limit to 20 messages per second (max = 30)
TELEGRAM_BROADCAST_LOGGING_PERIOD = 5  # sec

# ---------- Настройки админки ---------- #

#: Максимально количество приложений на странице
ADMIN_APPS_PER_PAGE = 5
#: Максимально количество моделей на странице
ADMIN_MODELS_PER_PAGE = 5
#: Максимально количество строк на странице
ADMIN_ROWS_PER_PAGE = 5

with suppress(ImportError):
    from configs import *  # noqa: F401,F403,RUF100

if ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_AVERAGE_INDEX not in (1, 2, 3, 4):
    raise ValueError("ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_AVERAGE_INDEX should be in (1, 2, 3, 4)")
