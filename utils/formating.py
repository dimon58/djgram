def __bytes_format(size: float, digits: int = 0) -> float | int:
    if digits == 0:
        return round(size)

    return round(size, digits)


def get_bytes_size_format(b: float, digits: int = 2) -> str:
    """
    Форматирует число байт в человекочитаемые единицы измерения
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < 1024:
            return f"{__bytes_format(digits)} {unit}B"
        b /= 1024
    return f"{__bytes_format(digits)} YB"
