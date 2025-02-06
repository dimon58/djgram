import logging
import os
import time
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from aiogram.types import BufferedInputFile, FSInputFile, InputFile
from djgram.utils.formating import get_bytes_size_format
from djgram.utils.input_file_ext import S3FileInput

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


class LoggingInputFile(InputFile):
    """
    Используется в качестве логирующего прокси для загрузки файла в телеграм
    """

    def __init__(self, input_file: InputFile, debounce_time: float = 5):  # noqa: D107
        super().__init__(filename=input_file.filename, chunk_size=input_file.chunk_size)
        self.real_input_file = input_file
        self.debounce_time = debounce_time

    def _try_get_size_bytes(self) -> int | None:
        if isinstance(self.real_input_file, BufferedInputFile):
            return len(self.real_input_file.data)

        if isinstance(self.real_input_file, FSInputFile):
            return os.path.getsize(self.real_input_file.path)  # noqa: PTH202

        if isinstance(self.real_input_file, S3FileInput):
            return self.real_input_file.obj.size

        return None

    async def read(self, bot: "Bot") -> AsyncGenerator[bytes, None]:
        # В случае использования локального сервера логирование будет не правильным,
        # так как файл сначала загружается на локальный сервер (скорее всего очень быстро),
        # а потом локальный сервер отправляет в телеграмм

        file_size = self._try_get_size_bytes()

        if file_size is not None:
            bsf = get_bytes_size_format(file_size)
        else:
            bsf = "N/A"
            file_size = float("nan")
        logger.info("Start uploading file with size %s", bsf)

        sent_bytes = 0

        _last_logging = float("-inf")
        _start = time.perf_counter()
        async for chunk in self.real_input_file.read(bot):
            sent_bytes += len(chunk)
            yield chunk

            now = time.perf_counter()
            if now > _last_logging + self.debounce_time:
                avg_speed = sent_bytes / (now - _start)
                logger.info(
                    "Uploaded %s (%.2f%%) (avg %s/s) eta %.2f sec",
                    get_bytes_size_format(sent_bytes),
                    100 * sent_bytes / file_size,
                    get_bytes_size_format(avg_speed),
                    (file_size - sent_bytes) / avg_speed,
                )
                _last_logging = now
        _elapsed = time.perf_counter() - _start

        logger.info(
            "File with size %s uploaded in %.2f sec (avg %s/s)",
            get_bytes_size_format(sent_bytes),
            _elapsed,
            get_bytes_size_format(sent_bytes / _elapsed),
        )
