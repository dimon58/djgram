import asyncio
from collections.abc import Coroutine


def run_async_from_sync(coro: Coroutine) -> None:
    """
    Запускает асинхронную функцию из синхронного кода

    Если есть запущенный event loop, то добавляет задачу в него,
    иначе создаёт новый и исполняет в нём
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)  # noqa: RUF006
    except RuntimeError:
        asyncio.run(coro)
