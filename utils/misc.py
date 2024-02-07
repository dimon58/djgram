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
    model.model_config["frozen"] = False
    yield
    model.model_config["frozen"] = True


async def try_run_async(
    coro: Awaitable[T],
    exception_class: type[Exception] | Sequence[type[Exception]] = Exception,
    max_attempts: int = 3,
) -> tuple[Literal[True], T] | tuple[Literal[False], None]:
    """
    Пытает выполнить корутину несколько раз, пока не получиться

    Args:
        coro: корутина, которую нужно выполнить
        exception_class: класс или классы исключений для отлавливания
        max_attempts: максимальное число попыток выполнить корутину

    Returns:
        (успешность выполнения, результат или None)
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return True, await coro
        except exception_class as exc:
            logger.exception("failed %s/%s attempt to run %s", attempt, max_attempts, coro, exc_info=exc)

    logger.error("Failed to run %s %s times", coro, max_attempts)

    return False, None
