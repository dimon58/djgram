import asyncio
import logging
import sys
import time
from datetime import UTC, datetime
from typing import TypeAlias

import aiohttp

from djgram.configs import (
    ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_AVERAGE_INDEX,
    ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_BOT_TABLE,
    ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_COLLECTION_PERIOD,
    ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_GENERAL_TABLE,
)
from djgram.db import clickhouse
from djgram.utils.async_tools import PeriodicTask

StatValueType: TypeAlias = int | float | str | datetime
StatDictType: TypeAlias = dict[str, StatValueType]

logger = logging.getLogger(__name__)
try:
    from configs import TELEGRAM_LOCAL_SERVER_STATS_URL
except ImportError:
    logger.critical("You need to specify TELEGRAM_LOCAL_SERVER_STATS_URL setting to collect stats from local server")
    sys.exit(1)

_mod = {
    "K": 1024,
    "M": 1024 * 1024,
    "G": 1024 * 1024 * 1024,
    "T": 1024 * 1024 * 1024 * 1024,
}


async def get_stats() -> str:
    """
    Возвращает текст со статистикой локального телеграм сервера

    Например:

    DURATION	inf	5sec	1min	1hour
    uptime	7199.051260
    bot_count	1
    active_bot_count	1
    rss	30868KB
    vm	43068KB
    rss_peak	30876KB
    vm_peak	43136KB
    total_cpu	1.386936%	1.166181%	1.190551%	1.386936%
    user_cpu	0.472083%	0.666389%	0.416276%	0.472083%
    system_cpu	0.914853%	0.499792%	0.774274%	0.914853%
    buffer_memory	89400B
    active_webhook_connections	0
    active_requests	0
    active_network_queries	0
    request_count	0.098749	0.000000	0.023310	0.098763
    request_bytes	35.706418	0.000000	7.295909	35.711378
    request_file_count	0.000000	0.000000	0.000000	0.000000
    request_files_bytes	0.000000	0.000000	0.000000	0.000000
    request_max_bytes	0	0	0	0
    response_count	0.098749	0.000000	0.023310	0.098763
    response_count_ok	0.098749	0.000000	0.023310	0.098763
    response_count_error	0.000000	0.000000	0.000000	0.000000
    response_bytes	2.339984	0.000000	2.459164	2.340309
    update_count	0.000000	0.000000	0.000000	0.000000

    id	1111111111
    uptime	7198.608074
    token	1111111111:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    username	bot1
    head_update_id	12345678
    request_count/sec	0.098755	0.000000	0.023310	0.098769
    update_count/sec	0.000000	0.000000	0.000000	0.000000

    id	2222222222
    uptime	7198.608074
    token	2222222222:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    username	bot2
    head_update_id	12345678
    request_count/sec	0.098755	0.000000	0.023310	0.098769
    update_count/sec	0.000000	0.000000	0.000000	0.000000
    """
    async with (
        aiohttp.ClientSession() as session,
        session.get(TELEGRAM_LOCAL_SERVER_STATS_URL) as resp,
    ):
        return (await resp.text()).strip()


def parse_value(text: str) -> StatValueType:  # noqa: PLR0911
    """
    Превращает значение из статистики в нужное представление
    """
    # bytes, KB, MB, etc to bytes
    if text.endswith("B"):
        if text[-2].isdigit():
            return int(text[:-1])
        return int(text[:-2]) * _mod[text[-2]]

    # smth usage percent
    if text.endswith("%"):
        return float(text[:-1])

    if text == "UNKNOWN":
        return 0.0

    try:
        return int(text)

    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


def parse_stats_block(text: str) -> StatDictType:
    """
    Парсит и возвращает блок статистики в удобном виде
    """
    result = {}

    for line in text.split("\n")[1:]:  # skip header: DURATION inf 5sec 1min 1hour
        values = line.split("\t")
        if len(values) > 2:
            result[values[0]] = parse_value(values[ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_AVERAGE_INDEX])
        else:
            result[values[0]] = parse_value(values[1])

    return result


def parse_stats(stats: str) -> tuple[StatDictType, ...]:
    """
    Парсит и возвращает неочищенную статистику локального телеграм сервера в виде (общая, бот1, бот2, бот3, ...)
    """
    return tuple(parse_stats_block(block) for block in stats.split("\n\n"))


async def collect_stats() -> tuple[StatDictType, ...]:
    """
    Возвращает очищенную статистику локального телеграм сервера в виде (общая, бот1, бот2, бот3, ...)
    """
    start = time.perf_counter()
    stats = await get_stats()
    end = time.perf_counter()
    now = datetime.now(tz=UTC)
    collection_time = end - start

    stats = parse_stats(stats)
    for stat in stats:
        stat["date"] = now
        stat["collection_time"] = collection_time

    for bot in stats[1:]:
        bot.pop("token")

        km = {}
        for key in bot:
            if "/" in key:
                km[key] = key.replace("/", "_per_")

        for orig, new in km.items():
            bot[new] = bot.pop(orig)

    return stats


async def collect_and_save() -> None:
    try:

        general, *bots = await collect_stats()

        async with clickhouse.connection() as clickhouse_connection:
            await clickhouse.insert_dict(
                clickhouse_connection,
                ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_GENERAL_TABLE,
                general,
            )

            for bot in bots:
                await clickhouse.insert_dict(
                    clickhouse_connection,
                    ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_BOT_TABLE,
                    bot,
                )

        logger.debug("Local server statistics saved to clickhouse")

    # pylint: disable=broad-exception-caught
    except Exception as exc:
        logger.exception(
            "Local server statistics saving to clickhouse error: %s: %s",
            exc.__class__.__name__,
            exc, # noqa: TRY401
            exc_info=exc,
        )
        return


async def run_telegram_local_server_stats_collection_in_background() -> None:
    logger.info(
        "Start local server statistics collection every %s sec",
        ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_COLLECTION_PERIOD,
    )
    task = PeriodicTask(collect_and_save, ANALYTICS_TELEGRAM_LOCAL_SERVER_STATS_COLLECTION_PERIOD)
    await asyncio.create_task(task.start())
