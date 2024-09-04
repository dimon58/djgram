-- Скрипт создания таблиц для сбора статистики update'ов telegram

CREATE TABLE IF NOT EXISTS update
(
    `date`                      DateTime64,
    `execution_time`            Float64,
    `event_type`                String,
    `content_type`              Nullable(String),

    `bot_id`                    Int64,
    `user_id`                   Nullable(Int64),
    `chat_id`                   Nullable(Int64),
    `thread_id`                 Nullable(Int64),
    `business_connection_id`    Nullable(Int64),
    `update_id`                 Int64,
    `event`                     String
)
    ENGINE = MergeTree()
        ORDER BY (date);
