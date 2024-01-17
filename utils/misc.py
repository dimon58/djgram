import datetime
import importlib
import operator
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any


def utcnow() -> datetime.datetime:
    """
    Возвращает текущую дату и время во временной зоне UTC
    """
    return datetime.datetime.now(tz=datetime.UTC)


def resolve_pyobj(str_path: str) -> Any:
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


class LazyObject:
    _wrapped = None
    _is_init = False

    def __init__(self, factory):
        """
        Args:
            factory: initializer for object
        """
        # Assign using __dict__ to avoid the setattr method.
        self.__dict__["_factory"] = factory

    def _setup(self):
        self._wrapped = self._factory()
        self._is_init = True

    @staticmethod
    def new_method_proxy(func):
        """
        Util function to help us route functions
        to the nested object.
        """

        def inner(self, *args):
            if not self._is_init:
                self._setup()
            return func(self._wrapped, *args)

        return inner

    def __setattr__(self, name, value):
        # These are special names that are on the LazyObject.
        # every other attribute should be on the wrapped object.
        if name in {"_is_init", "_wrapped"}:
            self.__dict__[name] = value
        else:
            if not self._is_init:
                self._setup()
            setattr(self._wrapped, name, value)

    def __delattr__(self, name):
        if name == "_wrapped":
            raise TypeError("can't delete _wrapped.")
        if not self._is_init:
            self._setup()
        delattr(self._wrapped, name)

    __getattr__ = new_method_proxy(getattr)
    __bytes__ = new_method_proxy(bytes)
    __str__ = new_method_proxy(str)
    __bool__ = new_method_proxy(bool)
    __dir__ = new_method_proxy(dir)
    __hash__ = new_method_proxy(hash)
    __class__ = property(new_method_proxy(operator.attrgetter("__class__")))
    __eq__ = new_method_proxy(operator.eq)
    __lt__ = new_method_proxy(operator.lt)
    __gt__ = new_method_proxy(operator.gt)
    __ne__ = new_method_proxy(operator.ne)
    __getitem__ = new_method_proxy(operator.getitem)
    __setitem__ = new_method_proxy(operator.setitem)
    __delitem__ = new_method_proxy(operator.delitem)
    __iter__ = new_method_proxy(iter)
    __len__ = new_method_proxy(len)
    __contains__ = new_method_proxy(operator.contains)


@dataclass
class MeasureResult:
    """
    Результат измерения времени с помощью measure_time
    """

    elapsed: float = 0

    def get_seconds_string(self):
        return f"Elapsed {self.elapsed:.2f} sec"

    def get_milliseconds_string(self):
        return f"Elapsed {self.elapsed * 1000:.2f} ms"

    def get_microseconds_string(self):
        return f"Elapsed {self.elapsed * 1000000:.2f} us"

    def get_nanoseconds_string(self):
        return f"Elapsed {self.elapsed * 1000000:.2f} ns"


@contextmanager
def measure_time() -> Generator[MeasureResult, None, None]:
    """
    Измеряет время с помощью контекстного менеджера


    with measure_time() as td:
        func()

    print("Прошло", td.elapsed, "сек")
    """
    res = MeasureResult()
    s = time.perf_counter()
    yield res
    e = time.perf_counter()

    res.elapsed = e - s
