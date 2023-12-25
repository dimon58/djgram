from contextlib import suppress

# Настройки базы данных
DB_URL = "sqlite+aiosqlite:///db.sqlite3"
DB_ENGINE_SETTINGS = {}
DB_METADATA = None
DB_SUPPORTS_ARRAYS = False

# Настройки clickhouse
CLICKHOUSE_HOST = "localhost"
CLICKHOUSE_PORT = 9000
CLICKHOUSE_DB = "default"
CLICKHOUSE_USER = None
CLICKHOUSE_PASSWORD = None

#: Таблица в clickhouse, в которую логируются все обновления телеграмм
#   https://core.telegram.org/bots/api#getting-updates
ANALYTICS_UPDATES_TABLE = "update"

#: Путь до папки с диаграммами диалогов
DIALOG_DIAGRAMS_DIR = "dialog_diagrams"

#: Включить генерацию диаграмм диалогов aiogram-dialogs
ENABLE_DIALOG_DIAGRAMS_GENERATION = True

#: Какое время пользователь считает активным для получения рассылки
ACTIVE_USER_TIMEOUT = 60 * 60 * 24 * 14

# ---------- Настройки админки ---------- #

#: Максимально количество приложений на странице
ADMIN_APPS_PER_PAGE = 5
#: Максимально количество моделей на странице
ADMIN_MODELS_PER_PAGE = 5
#: Максимально количество строк на странице
ADMIN_ROWS_PER_PAGE = 5

with suppress(ImportError):
    from configs import *  # noqa: F401,F403,RUF100
