CREATE TABLE IF NOT EXISTS general_statistics
(
    `date`                       DateTime64,
    `collection_time`            Float64,

    `active_bot_count`           UInt64,
    `active_network_queries`     UInt64,
    `active_requests`            UInt64,
    `active_webhook_connections` UInt64,
    `bot_count`                  UInt64,
    `buffer_memory`              UInt64,
    `request_bytes`              Float64,
    `request_count`              Float64,
    `request_file_count`         Float64,
    `request_files_bytes`        Float64,
    `request_max_bytes`          UInt64,
    `response_bytes`             Float64,
    `response_count_error`       Float64,
    `response_count_ok`          Float64,
    `response_count`             Float64,
    `rss_peak`                   UInt64,
    `rss`                        UInt64,
    `system_cpu`                 Float64,
    `total_cpu`                  Float64,
    `update_count`               Float64,
    `uptime`                     Float64,
    `user_cpu`                   Float64,
    `vm_peak`                    UInt64,
    `vm`                         UInt64
)
    ENGINE = MergeTree()
        ORDER BY (date);

CREATE TABLE IF NOT EXISTS bot_statistics
(
    `date`                  DateTime64,
    `collection_time`       Float64,

    `uptime`                Float64,
    `active_request_count`  UInt64 DEFAULT 0,
    `pending_update_count`  UInt64 DEFAULT 0,
    `head_update_id`        UInt64,
    `request_count_per_sec` Float64,
    `tail_update_id` Nullable(UInt64),
    `update_count_per_sec`  Float64,
    `username`              String
)
    ENGINE = MergeTree()
        ORDER BY (date);
