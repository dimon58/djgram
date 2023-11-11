import datetime


def utcnow() -> datetime.datetime:
    """
    Возвращает текущую дату и время во временной зоне UTC
    """
    return datetime.datetime.now(tz=datetime.UTC)


def resolve_pyobj(str_path: str) -> any:
    """
    Получает объект по пути

    Например, по пути "aiogram.type.Message" вернётся класс Message из модуля aiogram.type
    """
    *path, name = str_path.split(".")
    if len(path) == 0:
        raise ValueError("Incorrect path: %s", str_path)

    module = __import__(".".join(path))

    return getattr(module, name)
