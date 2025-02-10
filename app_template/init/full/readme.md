# Телеграм бот

Для запуска нужно установить [Docker](https://www.docker.com/)

и получить токен бота от [BotFather](https://core.telegram.org/bots/tutorial#obtain-your-bot-token)

## Запуск для разработки

1. Создаём файл с переменными окружения
   (при инициализации проекта он был создан автоматически,
   но для запуска в продашн нужно будет сделать самостоятельно)
   ```shell
   cp example.env .env
   ```

2. В файле `.env` прописываем полученный токен бота

3. Устанавливаем uv
   ```shell
   pip install uv
   ```

   или https://docs.astral.sh/uv/getting-started/installation/

4. Устанавливаем зависимости для python
   ```shell
   uv sync --dev
   ```
   После этой команды появится файл `uv.lock`, если его не было раньше. Его нужно добавить в git.
   ```shell
   git add uv.lock
   ```

5. Запускает docker контейнеры с базами данных

   ```shell
   docker compose up -d redis postgres clickhouse
   ```

6. Создаём и применяем миграции
   ```shell
   alembic revision --autogenerate
   alembic upgrade head
   ```

7. Запускаем бота
   ```shell
   python main.py
   ```

8. Для разработки стоит включить `pre-commit` для поддержки качества кода, если вы используйте `git`
   ```shell
   pre-commit install
   ```

## Запуск в продакшн

1. Создаём файл с переменными окружения
   ```shell
   cp example.env .env
   ```

2. В файле `.env` прописываем полученный токен бота и меняет пути до сервисов

   ```dotenv
   POSTGRES_HOST=postgres
   REDIS_HOST=redis
   CLICKHOUSE_HOST=clickhouse
   ```

   Хотя в `.env` можно не менять хосты,
   так как они в любом случае перезаписаны в `docker-compose.yaml`,
   но это будет хорошим тоном

3. Собираем бота
   ```shell
   docker compose build
   ```

4. Запускаем бота

   ```shell
   docker compose up
   ```
