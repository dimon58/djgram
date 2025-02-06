# Настройка локального Bot Api сервера

Это инструкция по использованию локального bot api сервера с помощью docker-compose

Полезные ссылки:

- https://github.com/tdlib/telegram-bot-api
- https://registry.hub.docker.com/r/aiogram/telegram-bot-api
- https://core.telegram.org/bots/api#using-a-local-bot-api-server

1. Добавляем в `docker-compose.yml` сервисы и volume

   ```yaml
   services:
     telegram-bot-api:
       image: aiogram/telegram-bot-api:latest
       hostname: telegram-bot-api
       pull_policy: always  # Обновляем каждый перезапуск для совместимости с телеграмм
       restart: unless-stopped
       volumes:
         - telegram-bot-api-data:/var/lib/telegram-bot-api
       env_file:
         - .env
       ports:
         - "8081:8081" # bot api
         - "8082:8082" # статистика

     nginx:
       image: nginx:1.27.2-alpine3.20-slim
       hostname: nginx
       restart: always
       depends_on:
         - telegram-bot-api
       volumes:
         - telegram-bot-api-data:/var/lib/telegram-bot-api:ro
         - ./docker/nginx:/etc/nginx/conf.d/:ro
         - ./logs/nginx:/var/log/nginx
       ports:
         - "8083:8083" # раздача файлов, для скачивания через local telegram bot api server
       profiles:
         - dev
         - production

   volumes:
     telegram-bot-api-data:
   ```

2. В `.env` прописываем его настройки. Подробнее https://registry.hub.docker.com/r/aiogram/telegram-bot-api

   ```dotenv
   # Настройки локального сервера bot api
   TELEGRAM_API_ID=...
   TELEGRAM_API_HASH=...
   TELEGRAM_LOCAL_SERVER_URL="http://localhost:8081"
   TELEGRAM_LOCAL_SERVER_STATS_URL="http://localhost:8082"
   TELEGRAM_LOCAL_SERVER_FILES_URL="http://localhost:8083"
   TELEGRAM_STAT=1
   TELEGRAM_LOCAL=0
   ```

   `TELEGRAM_LOCAL=0` стоит использовать, чтобы скачивать файлы по сети из локального сервера.
   Иначе нужно будет предоставить доступ к файловой системе сервера.
   Это можно сделать прописав volume в `docker-compose.yml`, но способ с nginx проще.

   На Windows не получится прописать volume,
   так как в данных сервера для каждого бота хранится своя папка с названием в виде токена бота.
   Токен бота имеет вид `1234567890:random-string`, а `:` нельзя использовать в пути файлов на Windows.

3. В папку в `docker/nginx` добавляем файлы `default.conf` с содержимым

   ```nginx configuration
   # Based on https://github.com/aiogram/telegram-bot-api/blob/master/example/nginx/default.conf
   # use $sanitized_request instead of $request to hide Telegram token
   log_format token_filter '$remote_addr - $remote_user [$time_local] '
                           '"$sanitized_request" $status $body_bytes_sent '
                           '"$http_referer" "$http_user_agent"';

   upstream telegram-local-server {
       server telegram-bot-api:8081;
   }

   server {
       listen 8083;
       listen [::]:8083;
       server_name _;

       chunked_transfer_encoding on;
       proxy_connect_timeout 600;
       proxy_send_timeout 600;
       proxy_read_timeout 600;
       send_timeout 600;
       client_max_body_size 2G;
       client_body_buffer_size 30M;
       keepalive_timeout 0;

       set $sanitized_request $request;
       if ( $sanitized_request ~ (\w+)\s(\/bot\d+):[-\w]+\/(\S+)\s(.*) ) {
           set $sanitized_request "$1 $2:<hidden-token>/$3 $4";
       }
       access_log /var/log/nginx/access.log token_filter;

       location ~* \/file\/bot\d+:(.*) {
           rewrite ^/file\/bot(.*) /$1 break;
           try_files $uri @files;
       }

       location / {
           try_files $uri @api;
       }

       location @files {
           root /var/lib/telegram-bot-api;
           gzip on;
           gzip_vary on;
           gzip_proxied any;
           gzip_comp_level 6;
           gzip_buffers 64 8k;
           gzip_http_version 1.1;
           gzip_min_length 1100;
       }

       location @api {
           proxy_pass  http://telegram-local-server;
           proxy_redirect off;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Host $server_name;
       }
   }
      ```

4. В `configs.py` прописываем

   ```python
   import os


   TELEGRAM_LOCAL: bool = bool(int(os.environ["TELEGRAM_LOCAL"]))
   TELEGRAM_LOCAL_SERVER_URL: str = os.environ["TELEGRAM_LOCAL_SERVER_URL"]
   TELEGRAM_LOCAL_SERVER_STATS_URL: str = os.environ["TELEGRAM_LOCAL_SERVER_STATS_URL"]
   TELEGRAM_LOCAL_SERVER_FILES_URL: str = os.environ["TELEGRAM_LOCAL_SERVER_FILES_URL"]
   ```

5. Прописываем использование бота в коде

   ```python
   from djgram.contrib.local_server.local_bot import get_local_bot

   from configs import (
       TELEGRAM_BOT_TOKEN,
       TELEGRAM_LOCAL,
       TELEGRAM_LOCAL_SERVER_FILES_URL,
       TELEGRAM_LOCAL_SERVER_URL,
   )


   async def main():
       ...

       bot = get_local_bot(
           telegram_bot_token=TELEGRAM_BOT_TOKEN,
           telegram_local=TELEGRAM_LOCAL,
           telegram_local_server_url=TELEGRAM_LOCAL_SERVER_URL,
           telegram_local_server_files_url=TELEGRAM_LOCAL_SERVER_FILES_URL,
       )

       ...

       await dp.start_polling(bot, skip_updates=False)
   ```

6. Для автоматического сбора статистики при запуске бота прописываем

   ```python
   from djgram.contrib.analytics.local_server import run_telegram_local_server_stats_collection_in_background


   async def main():

       # Инициализация бота
       # ...

       await run_telegram_local_server_stats_collection_in_background()
       await dp.start_polling(bot, skip_updates=False)
   ```
