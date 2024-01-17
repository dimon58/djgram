# Телеграм бот

## Запуск

1. Получаем токен бота от [BotFather](https://core.telegram.org/bots/tutorial#obtain-your-bot-token)

2. В файле `.env` прописываем полученный токен бота

3. Устанавливаем зависимости для python
   ```shell
   pip install -r requirements-dev.txt
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