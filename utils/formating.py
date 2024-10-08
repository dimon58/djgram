from collections.abc import Callable
from datetime import date, datetime, timedelta

MINUTES_IN_HOUR = 60

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = MINUTES_IN_HOUR * SECONDS_IN_MINUTE
HOURS_IN_DAY = 24
SECONDS_IN_DAY = HOURS_IN_DAY * SECONDS_IN_HOUR
DAYS_IN_WEEK = 7
SECONDS_IN_WEEK = DAYS_IN_WEEK * SECONDS_IN_DAY


def __bytes_format(size: float, digits: int = 0) -> float | int:
    if digits == 0:
        return round(size)

    return round(size, digits)


def get_bytes_size_format(size: float, digits: int = 2, stop_at: str | None = None) -> str:
    """
    Форматирует число байт в человекочитаемые единицы измерения
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if size < 1024 or unit == stop_at:  # noqa: PLR2004
            return f"{__bytes_format(size, digits)} {unit}B"
        size /= 1024
    return f"{__bytes_format(size, digits)} YB"


def get_default_word_builder(
    word_0: str,
    word_1: str,
    word_234: str,
) -> Callable[[int], str]:
    """
    Создаёт функции для постановки существительного в нужное число

    Например:
    0 чатов
    1 чат
    2 чата
    3 чата
    4 чата
    5 чатов
    6 чатов
    7 чатов
    8 чатов
    9 чатов
    10 чатов
    11 чатов
    12 чатов
    13 чатов
    14 чатов
    15 чатов
    16 чатов
    17 чатов
    18 чатов
    19 чатов
    20 чатов
    21 чат
    ...
    """

    def inner(number: int) -> str:
        """
        Ставит слово "чат" в нужное число в зависимости от number. Например:
        """
        number %= 100
        if 5 <= number <= 20:  # noqa: PLR2004
            return word_0

        number %= 10

        if number == 1:
            return word_1

        if 2 <= number <= 4:  # noqa: PLR2004
            return word_234

        return word_0

    return inner


get_day_word = get_default_word_builder("дней", "день", "дня")
get_week_word = get_default_word_builder("недель", "неделя", "недели")


def seconds_to_human_readable(seconds: float) -> str:
    """
    Возвращает человекочитаемое представление числа секунд в строке вида "3 дня 1 ч 15 мин"

    >>> seconds_to_human_readable(1.5)
    '0 сек'

    >>> seconds_to_human_readable(0)
    '0 сек'

    >>> seconds_to_human_readable(123)
    '2 мин 3 сек'

    >>> seconds_to_human_readable(7320)
    '2 ч 2 мин'

    >>> seconds_to_human_readable(86400)
    '1 день'

    >>> seconds_to_human_readable(1209600)
    '2 недели'
    """

    ms = round(seconds * 1000)
    seconds = ms // 1000
    ms %= 1000

    weeks, remainder = divmod(seconds, SECONDS_IN_WEEK)
    days, remainder = divmod(remainder, SECONDS_IN_DAY)
    hours, remainder = divmod(remainder, SECONDS_IN_HOUR)
    minutes, seconds = divmod(remainder, SECONDS_IN_MINUTE)

    result = []
    if weeks > 0:
        result.append(f"{weeks} {get_week_word(weeks)}")
    if days > 0:
        result.append(f"{days} {get_day_word(days)}")
    if hours > 0:
        result.append(f"{hours} ч")
    if minutes > 0:
        result.append(f"{minutes} мин")
    if ms == 0 and (seconds > 0 or len(result) == 0):
        result.append(f"{seconds} сек")
    if ms > 0:
        result.append(f"{ms} мс")

    return " ".join(result)


def timedelta_to_human_readable(delta: timedelta) -> str:
    """
    Аналогично seconds_to_human_readable, но работает с timedelta
    """
    return seconds_to_human_readable(delta.total_seconds())


_month_to_name_rus = [
    "dummy",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]


def date_to_human_readable(date_: date | datetime):
    """
    Превращает дату в строку вида "6 сентября 2024"
    """
    return f"{date_.day} {_month_to_name_rus[date_.month]} {date_.year}"


def datetime_to_human_readable(datetime_: datetime, with_seconds: bool = True) -> str:
    """
    Превращает дату в строку вида "4 октября 2024 17:14" или 4 октября 2024 17:14:28"
    """
    text = f"{date_to_human_readable(datetime_)} {datetime_.hour}:{datetime_.minute:02}"

    if with_seconds:
        return f"{text}:{datetime_.second:02}"

    return text
