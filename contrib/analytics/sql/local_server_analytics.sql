-- Скрипт создания таблиц для сбора статистики локального сервера bot api

CREATE TABLE IF NOT EXISTS local_server_general_statistics
(
    `date`                          DateTime64,
    `collection_time`               Float64,
    `duration`                      Int32,

-- Взято из https://github.com/tdlib/telegram-bot-api/blob/master/telegram-bot-api/ClientManager.cpp#L223
    `uptime`                        Float64,
    `bot_count`                     UInt64,
    `active_bot_count`              Int32,

    `rss`                           UInt64,
    `vm`                            UInt64,
    `rss_peak`                      UInt64,
    `vm_peak`                       UInt64,

    `buffer_memory`                 UInt64,
    `active_webhook_connections`    Int64,
    `active_requests`               UInt64,
    `active_network_queries`        UInt64,

-- Взято из  https://github.com/tdlib/telegram-bot-api/blob/master/telegram-bot-api/Stats.cpp#L52
    `total_cpu`                     Float64 DEFAULT Nan,
    `user_cpu`                      Float64 DEFAULT Nan,
    `system_cpu`                    Float64 DEFAULT Nan,

    `request_count`                 Float64 DEFAULT 0,
    `request_bytes`                 Float64 DEFAULT 0,
    `request_file_count`            Float64 DEFAULT 0,
    `request_files_bytes`           Float64 DEFAULT 0,
    `request_max_bytes`             Int64 DEFAULT 0,
    `response_count`                Float64 DEFAULT 0,
    `response_count_ok`             Float64 DEFAULT 0,
    `response_count_error`          Float64 DEFAULT 0,
    `response_bytes`                Float64 DEFAULT 0,
    `update_count`                  Float64 DEFAULT 0

)
    ENGINE = MergeTree()
        ORDER BY (date);

CREATE TABLE IF NOT EXISTS local_server_bot_statistics
(
    `date`                      DateTime64,
    `collection_time`           Float64,
    `duration`                      Int32,

-- Взято из https://github.com/tdlib/telegram-bot-api/blob/master/telegram-bot-api/ClientManager.cpp#L261
    `id`                        UInt64,
    `uptime`                    Float64,
-- Не стоит сохранять токен
--     `token`                     String,
    `username`                  String,
    `active_request_count`      Int64 DEFAULT 0,
    `active_file_upload_bytes`  Int64 DEFAULT 0,
    `active_file_upload_count`  Int64 DEFAULT 0,
    `webhook`                   String DEFAULT '',
    `has_custom_certificate`    Boolean DEFAULT False,
    `webhook_max_connections`   Int32 DEFAULT 0,
    `head_update_id`            Int32 DEFAULT 0,
    `tail_update_id`            Int32 DEFAULT 0,
    `pending_update_count`      UInt64 DEFAULT 0,

    `update_count_per_sec`      Float64 DEFAULT 0,
    `request_count_per_sec`     Float64 DEFAULT 0
)
    ENGINE = MergeTree()
        ORDER BY (date);
