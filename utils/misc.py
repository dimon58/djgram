import asyncio
import datetime
import importlib
import logging
import time
from collections.abc import Awaitable, Generator, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Literal, TypeVar

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


@contextmanager
def unfreeze_model(model: BaseModel) -> Iterator[None]:
    """
    Делает модель pydantic доступной для изменения
    """
    frozen = model.model_config.get(_FROZEN_KEY, False)
    model.model_config[_FROZEN_KEY] = False
    yield
    model.model_config[_FROZEN_KEY] = frozen


async def try_run_async(
    coro: Awaitable[T],
    max_attempts: int = 3,
    exception_class: type[Exception] | Sequence[type[Exception]] = Exception,
    sleep_time: float = 0.0,
) -> tuple[Literal[True], T] | tuple[Literal[False], None]:
    """
    Пытается выполнить функцию несколько раз и вернуть её результат, пока не получиться

    Args:
        coro: корутина, которую нужно запустить
        max_attempts: максимальное число попыток выполнить
        exception_class: ожидаемый класс или классы исключений
        sleep_time: время ожидания между попытками

    Returns:
        Успешность выполнения, результат или None
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
