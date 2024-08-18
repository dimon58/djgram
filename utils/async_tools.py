import asyncio
import time
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import Any


class PeriodicTask:
    """
    Периодическая задача для asyncio

    Запуск:

    task = PeriodicTask(func, interval)
    await asyncio.create_task(task.start())


    https://stackoverflow.com/questions/37512182/how-can-i-periodically-execute-a-function-with-asyncio
    """

    def __init__(self, func: Callable[[], Awaitable[Any]], period: float):
        """
        Args:
            func: Асинхронная функция без аргументов
            period: Период выполнения. Если функция работает дольше, чем период, то будут проблемы.
        """
        self.func = func
        self.period = period

        self._is_started = False
        self._task = None

    async def start(self) -> None:
        if self._is_started:
            return

        self._is_started = True
        # Start task to call func periodically:
        self._task = asyncio.ensure_future(self._run())

    async def stop(self) -> None:
        if not self._is_started:
            return

        self._is_started = False
        # Stop task and await it stopped:
        self._task.cancel()  # pyright: ignore [reportOptionalMemberAccess]
        with suppress(asyncio.CancelledError):
            await self._task  # pyright: ignore [reportGeneralTypeIssues]

    async def _run(self) -> None:

        # Делаем, чтобы выполнялось именно раз в период, без отклонений частоты
        first_call = time.perf_counter()
        iters = 0
        while True:
            await self.func()
            iters += 1
            await asyncio.sleep(first_call + iters * self.period - time.perf_counter())
