-- Скрипт создания таблиц для сбора статистики update'ов telegram
-- noinspection SqlResolveForFile @ object-type/"JSON"

SET allow_experimental_object_type = 1;


CREATE TABLE IF NOT EXISTS update
(
    `date`                      DateTime64,
    `execution_time`            Float64,
    `event_type`                String,
    `content_type`              Nullable(String),

    `update_id`                 Int64,
    `message`                   JSON,
    `edited_message`            JSON,
    `channel_post`              JSON,
    `edited_channel_post`       JSON,
    `message_reaction`          JSON,
    `message_reaction_count`    JSON,
    `inline_query`              JSON,
    `chosen_inline_result`      JSON,
    `callback_query`            JSON,
    `shipping_query`            JSON,
    `pre_checkout_query`        JSON,
    `poll`                      JSON,
    `poll_answer`               JSON,
    `my_chat_member`            JSON,
    `chat_member`               JSON,
    `chat_join_request`         JSON,
    `chat_boost`                JSON,
    `removed_chat_boost`        JSON
)
    ENGINE = MergeTree()
        ORDER BY (date);
