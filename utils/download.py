import logging
from io import BytesIO

from aiogram import Bot

from djgram.utils.formating import get_bytes_size_format
from djgram.utils.misc import measure_time

logger = logging.getLogger(__name__)


async def download_file(bot: Bot, file_id: str, file_size: int) -> BytesIO:
    """
    Скачивает файл и записывает его в буфер
    """
    bsf = get_bytes_size_format(file_size)
    logger.info("Start downloading file %s with size %s", file_id, bsf)

    buffer = BytesIO()

    with measure_time() as td:
        await bot.download(file_id, buffer)

    logger.info(
        "Downloaded file %s with size %s in %.2f sec (avg %s/s)",
        file_id,
        bsf,
        td.elapsed,
        get_bytes_size_format(file_size / td.elapsed),
    )

    return buffer
