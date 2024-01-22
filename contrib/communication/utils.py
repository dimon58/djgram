from djgram.utils.translation import get_default_word_builder

get_user_word = get_default_word_builder("пользователям", "пользователю", "пользователям")
get_kotoriy_bil_activniy_word = get_default_word_builder(
    "которые были активны", "который был активен", "которые были активны"
)
get_day_word = get_default_word_builder("дней", "день", "дня")
get_week_word = get_default_word_builder("недель", "неделя", "недели")


def get_seconds_word(seconds: int) -> str:
    """
    Возвращает человекочитаемое представление числа секунд

    >>> get_seconds_word(0)
    '0 сек'

    >>> get_seconds_word(123)
    '2 мин 3 сек'

    >>> get_seconds_word(7320)
    '2 ч 2 мин'

    >>> get_seconds_word(86400)
    '1 день'

    >>> get_seconds_word(1209600)
    '2 недели'
    """
    weeks, remainder = divmod(seconds, 7 * 24 * 3600)
    days, remainder = divmod(remainder, 24 * 3600)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    result = []
    if weeks > 0:
        result.append(f"{weeks} {get_week_word(weeks)}")
    if days > 0:
        result.append(f"{days} {get_day_word(days)}")
    if hours > 0:
        result.append(f"{hours} ч")
    if minutes > 0:
        result.append(f"{minutes} мин")
    if seconds > 0 or len(result) == 0:
        result.append(f"{seconds} сек")

    return " ".join(result)
