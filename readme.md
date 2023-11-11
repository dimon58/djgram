Требует наличие файла `configs.py` в корне проекта

В нем должны быть настройки

```python
# ---------- База данных ---------- #
# https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
DB_URL = "sqlite:///db.sqlite3"
DB_SCHEMA = None
# https://stackoverflow.com/questions/24956894/sql-alchemy-queuepool-limit-overflow
DB_ENGINE_POOL_SIZE = 25

# Данные для подключения к ClickHouse
CLICKHOUSE_HOST = "localhost"
CLICKHOUSE_PORT = 9000
CLICKHOUSE_DB = "default"
CLICKHOUSE_USER = "default"
CLICKHOUSE_PASSWORD = "password"
```