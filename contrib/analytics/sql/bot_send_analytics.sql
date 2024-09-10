CREATE TABLE IF NOT EXISTS bot_send_analytics
(
    `update_id`                 Nullable(Int64),
    `bot_id`                    Int64,
    `date`                      DateTime64,
    `method`                    String,
    `method_data`               String,
    `request_timeout`           Nullable(Int64),
    `execution_time`            Float64,
    `answer`                    String,
)
    ENGINE = MergeTree()
        ORDER BY (date);
