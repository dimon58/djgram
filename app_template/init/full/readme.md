# Телеграм бот

Для запуска нужно установить [Docker](https://www.docker.com/)

и получить токен бота от [BotFather](https://core.telegram.org/bots/tutorial#obtain-your-bot-token)

## Запуск для разработки

1. В файле `.env` прописываем полученный токен бота

2. Устанавливаем зависимости для python
   ```shell
   pip install -r requirements-dev.txt
   ```

3. Запускает docker контейнеры с базами данных

   ```shell
   docker compose up -d redis postgres clickhouse
   ```

4. Создаём и применяем миграции
   ```shell
   alembic revision --autogenerate
   alembic upgrade head
   ```

5. Запускаем бота
   ```shell
   python main.py
   ```

6. Для разработки стоит включить `pre-commit` для поддержки качества кода, если вы используйте `git`
   ```shell
   pre-commit install
   ```

## Запуск в продакшн

1. В файле `.env` прописываем полученный токен бота и меняет пути до сервисов

   ```dotenv
   POSTGRES_HOST=postgres
   REDIS_HOST=redis
   CLICKHOUSE_HOST=clickhouse
   ```

2. Собираем бота
   ```shell
   docker compose build
   ```

3. Запускаем бота

   При работе на windows нужно поменять переносы строки файла `entrypoint.sh` на `LF`

   ```shell
   docker compose up
   ```

