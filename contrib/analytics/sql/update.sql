-- Скрипт создания таблиц для сбора статистики update'ов telegram
-- noinspection SqlResolveForFile @ object-type/"JSON"

SET allow_experimental_object_type = 1;


CREATE TABLE IF NOT EXISTS update
(
    `date`                      DateTime64,
    `execution_time`            Float64,
    `event_type`                String,
    `content_type`              Nullable(String),

    `user_id`                   Nullable(Int64),
    `chat_id`                   Nullable(Int64),
    `update_id`                 Int64,
    `event`                     JSON,
)
    ENGINE = MergeTree()
        ORDER BY (date);
