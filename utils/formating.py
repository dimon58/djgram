from datetime import timedelta

from service.utils import MINUTES_IN_HOUR

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = MINUTES_IN_HOUR * SECONDS_IN_MINUTE
HOURS_IN_DAY = 24


def __bytes_format(size: float, digits: int = 0) -> float | int:
    if digits == 0:
        return round(size)

    return round(size, digits)


def get_bytes_size_format(size: float, digits: int = 2) -> str:
    """
    Форматирует число байт в человекочитаемые единицы измерения
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if size < 1024:  # noqa: PLR2004
            return f"{__bytes_format(size, digits)} {unit}B"
        size /= 1024
    return f"{__bytes_format(size, digits)} YB"


def get_day_word(days: int) -> str:
    """
    Возвращает слово "день" согласованное с числом days

    0 - дней
    1 - день
    2 - дня
    3 - дня
    4 - дня
    5 - дней
    6 - дней
    7 - дней
    8 - дней
    9 - дней
    10 - дней
    11 - дней
    12 - дней
    13 - дней
    14 - дней
    15 - дней
    16 - дней
    17 - дней
    18 - дней
    19 - дней
    20 - дней
    21 - день
    22 - дня
    ...
    """

    days %= 100

    if days == 0:
        return "дней"

    if 5 <= days <= 20:
        return "дней"

    days %= 10

    if days == 1:
        return "день"

    if 2 <= days <= 4:
        return "дня"

    return "дней"


def seconds_to_human_readable(seconds: float) -> str:
    """
    Превращает число секунд в строку вида "3 дня 1 ч 15 мин"
    """

    seconds = int(seconds)

    if seconds < SECONDS_IN_MINUTE:
        return str(seconds)

    minutes = seconds // SECONDS_IN_MINUTE
    hours = minutes // MINUTES_IN_HOUR
    days = hours // HOURS_IN_DAY

    seconds %= SECONDS_IN_MINUTE
    minutes %= MINUTES_IN_HOUR
    hours %= HOURS_IN_DAY

    res = []

    if days > 0:
        res.append(f"{days} {get_day_word(days)}")

    if hours > 0:
        res.append(f"{hours} ч")

    if minutes > 0:
        res.append(f"{minutes} мин")

    if seconds > 0:
        res.append(f"{seconds} сек")

    return " ".join(res)


def timedelta_to_human_readable(delta: timedelta) -> str:
    """
    Аналогично seconds_to_human_readable, но работает с timedelta
    """
    return seconds_to_human_readable(delta.total_seconds())
