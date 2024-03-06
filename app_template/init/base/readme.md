# Телеграм бот

## Запуск

1. Получаем токен бота от [BotFather](https://core.telegram.org/bots/tutorial#obtain-your-bot-token)

2. Создаём файл с переменными окружения
   (при инициализации проекта он был создан автоматически, 
   но для запуска в продашн нужно будет сделать самостоятельно)
   ```shell
   cp example.env .env
   ```

3. В файле `.env` прописываем полученный токен бота

4. Устанавливаем зависимости для python
   ```shell
   pip install -r requirements-dev.txt
   ```

5. Создаём и применяем миграции
   ```shell
   alembic revision --autogenerate
   alembic upgrade head
   ```

6. Запускаем бота
   ```shell
   python main.py
   ```

7. Для разработки стоит включить `pre-commit` для поддержки качества кода, если вы используйте `git`
   ```shell
   pre-commit install
   ```