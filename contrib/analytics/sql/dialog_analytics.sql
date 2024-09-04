-- Скрипт создания таблиц для сбора статистики update'ов telegram

CREATE TABLE IF NOT EXISTS dialog_analytics
(
    `date`                                      DateTime64,
    `update_id`                                 Int64,
    `callback_query`                            Nullable(String),
    `message`                                   Nullable(String),
    `processor`                                 String,
    `processed`                                 Boolean,
    `process_time`                              Nullable(Float32),
    `not_processed_reason`                      Nullable(String),

    -- User info
    `telegram_user_id`                          Nullable(Int64),
    `telegram_chat_id`                          Nullable(Int64),
    `telegram_thread_id`                        Nullable(Int64),
    `telegram_business_connection_id`           Nullable(Int64),
    `user_id`                                   Nullable(Int64),

    -- Widget info
    `states_group_name`                         String,
    -- Если отправить сообщение, когда в текущем состоянии диалога нет виджета ввода,
    -- тогда отправляется в виртуальный MessageInput с widget_id = None
    `widget_id`                                 Nullable(String),
    `widget_type`                               String,
    `widget_text`                               Nullable(String),
    -- Additional widget info
    `calendar_user_config_firstweekday`         Nullable(Int8),
    `calendar_user_config_timezone_name`        LowCardinality(Nullable(String)),
    `calendar_user_config_timezone_offset`      Nullable(Int32),

    `aiogd_original_callback_data`              Nullable(String),

    -- aiogram_dialog.api.entities.Context
    `aiogd_context_intent_id`                   String,
    `aiogd_context_stack_id`                    String,
    `aiogd_context_state`                       String,
    `aiogd_context_start_data`                  String,
    `aiogd_context_dialog_data`                 String,
    `aiogd_context_widget_data`                 String,

    -- aiogram_dialog.api.entities.Stack
    `aiogd_stack_id`                            String,
    `aiogd_stack_intents`                       Array(String),
    `aiogd_stack_last_message_id`               Nullable(Int64),
    `aiogd_stack_last_reply_keyboard`           Boolean,
    `aiogd_stack_last_media_id`                 Nullable(String),
    `aiogd_stack_last_media_unique_id`          Nullable(String),
    `aiogd_stack_last_income_media_group_id`    Nullable(String)
)
    ENGINE = MergeTree()
        ORDER BY (date);
