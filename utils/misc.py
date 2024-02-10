import asyncio
import datetime
import importlib
import logging
import operator
import time
from collections.abc import Awaitable, Callable, Sequence
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from typing import Any, Self, TypeVar

from pydantic import BaseModel

T = TypeVar("T")
_FROZEN_KEY = "frozen"
logger = logging.getLogger(__name__)


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

    def __init__(self, factory: Callable | type):
        """
        Args:
            factory: initializer for object
        """
        # Assign using __dict__ to avoid the setattr method.
        self.__dict__["_factory"] = factory

    def _setup(self) -> None:
        self._wrapped = self._factory()
        self._is_init = True

    @staticmethod
    def new_method_proxy(func: Callable[..., T]) -> Callable[..., T]:
        """
        Util function to help us route functions
        to the nested object.
        """

        def inner(self: Self, *args, **kwargs) -> T:
            if not self._is_init:
                self._setup()
            return func(self._wrapped, *args, **kwargs)

        return inner

    def __setattr__(self, name: str, value: Any):
        # These are special names that are on the LazyObject.
        # every other attribute should be on the wrapped object.
        if name in {"_is_init", "_wrapped"}:
            self.__dict__[name] = value
        else:
            if not self._is_init:
                self._setup()
            setattr(self._wrapped, name, value)

    def __delattr__(self, name: str):
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

    def get_seconds_string(self) -> str:
        return f"Elapsed {self.elapsed:.2f} sec"

    def get_milliseconds_string(self) -> str:
        return f"Elapsed {self.elapsed * 1000:.2f} ms"

    def get_microseconds_string(self) -> str:
        return f"Elapsed {self.elapsed * 1000000:.2f} us"

    def get_nanoseconds_string(self) -> str:
        return f"Elapsed {self.elapsed * 1000000:.2f} ns"


@contextmanager
def measure_time() -> AbstractContextManager[MeasureResult]:
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


@contextmanager
def unfreeze_model(model: BaseModel) -> AbstractContextManager[None]:
    frozen = model.model_config[_FROZEN_KEY]
    model.model_config[_FROZEN_KEY] = False
    yield
    model.model_config[_FROZEN_KEY] = frozen


async def try_run_async(
    coro: Awaitable[T],
    max_attempts: int = 3,
    exception_class: type[Exception] | Sequence[type[Exception]] = Exception,
    sleep_time: float = 0.0,
) -> tuple[True, T] | tuple[False, None]:
    """
    Пытается выполнить функцию несколько раз и вернуть её результат

    Args:
        coro: корутина, которую нужно запустить
        max_attempts: максимальное число попыток выполнить
        exception_class: ожидаемый класс или классы исключений
        sleep_time: время ожидания между попытками

    Returns:
        Успешность выполнения и результат
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return True, await coro
        except exception_class as exc:
            logger.exception("[attempt %s/%s] Failed to run %s", attempt, max_attempts, coro, exc_info=exc)

        if sleep_time and attempt < max_attempts:
            await asyncio.sleep(sleep_time)

    logger.error("%s failed %s times", coro, max_attempts)

    return False, None
