import datetime
import importlib


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

    idx = str_path.rfind(".")

    if idx == "-1":
        raise ValueError('You should specify object importing from module. For example "module.AnyName"')

    path = str_path[:idx]
    name = str_path[idx + 1 :]

    module = importlib.import_module(path)

    return getattr(module, name)
