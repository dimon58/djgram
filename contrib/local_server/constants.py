from enum import IntEnum


class TelegramLocalServerStatsAverage(IntEnum):
    """
    Время усреднения статистики

    https://github.com/tdlib/telegram-bot-api/blob/master/telegram-bot-api/Stats.h#L60
    """

    INF = 1
    FIVE_SECOND = 2
    ONE_MINUTE = 3
    ONE_HOUR = 4
