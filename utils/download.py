import logging
from io import BytesIO

from aiogram import Bot
from aiogram.types import Downloadable

from djgram.utils.formating import get_bytes_size_format
from djgram.utils.misc import measure_time

logger = logging.getLogger(__name__)


async def download_file(
    bot: Bot,
    file: str | Downloadable,
    file_size: int,
    timeout: int = 30,
    chunk_size: int = 65536,
    seek: bool = True,
) -> BytesIO:
    """
    Скачивает файл и записывает его в буфер
    """
    bsf = get_bytes_size_format(file_size)
    file_id = file if isinstance(file, str) else file.file_id
    logger.info("Start downloading file %s with size %s", file_id, bsf)

    buffer = BytesIO()

    with measure_time() as td:
        await bot.download(file=file_id, destination=buffer, timeout=timeout, chunk_size=chunk_size, seek=seek)

    logger.info(
        "Downloaded file %s with size %s in %.2f sec (avg %s/s)",
        file_id,
        bsf,
        td.elapsed,
        get_bytes_size_format(file_size / td.elapsed),
    )

    return buffer
