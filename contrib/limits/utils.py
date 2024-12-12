import asyncio
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, Protocol, TypeVar

from limiter import Limiter

T = TypeVar("T")
P = ParamSpec("P")

logger = logging.getLogger(__name__)


class HasRetryAfterError(Protocol):  # noqa: D101
    retry_after: float | None


def limit_retry_call(  # noqa: ANN201
    retry_exception_class: type[HasRetryAfterError],
    max_rate: float,
    burst: int = 1,
    max_retries: int = 0,
    sleep_gap: float = 0.1,
    default_retry_after_time: float = 5,
):
    """
    A decorator to control the rate of an async function and handle rate-limiting exceptions.

    :param retry_exception_class: Exception class with a `retry_after` attribute (in seconds) indicating
                                  how long to wait before retrying. Should adhere to the `HasRetryAfter` protocol.

    :param max_rate: The maximum number of requests per second.
                     Corresponds to the token replenishment rate in the Limiter.

    :param burst: The capacity of the token bucket, allowing for brief bursts of requests.
                  Corresponds to the `capacity` in the Limiter.

    :param max_retries: The maximum number of retries if the function hits a rate limit. Raises the exception
                        after this number is exceeded.

    :param sleep_gap: Additional wait time (in seconds) added to the `retry_after` before retrying.

    :param default_retry_after_time: default sleep time in seconds if exc.retry_after is None

    :return: The decorated async function that will be rate-limited and handle retries.
    """

    def wrapper(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        _limiter = Limiter(max_rate, burst)

        _retry_after_event = asyncio.Event()
        _retry_after_event.set()

        @wraps(func)
        async def inner(*args: P.args, **kwargs: P.kwargs) -> T:  # pyright: ignore [reportReturnType]
            for attempt in range(max_retries + 1):  # noqa: RET503
                try:
                    await _retry_after_event.wait()
                    async with _limiter:
                        return await func(*args, **kwargs)
                except retry_exception_class as exc:  # pyright: ignore [reportGeneralTypeIssues]
                    if attempt == max_retries:
                        logger.exception(
                            "Rate limit hit after maximum of %d retries",
                            max_retries,
                            exc_info=exc,  # pyright: ignore [reportArgumentType]
                        )
                        raise

                    logger.info(exc)
                    # Make sure we don't allow other requests to be processed
                    _retry_after_event.clear()
                    await asyncio.sleep(
                        exc.retry_after + sleep_gap if exc.retry_after is not None else default_retry_after_time,
                    )

                finally:
                    # Allow other requests to be processed
                    _retry_after_event.set()

        return inner

    return wrapper
