from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from aiogram.types.input_file import DEFAULT_CHUNK_SIZE, InputFile

if TYPE_CHECKING:
    from aiogram import Bot
    from libcloud.storage.base import Object


class S3FileInput(InputFile):
    """
    Файл, загружаемы из S3 через libcloud
    """

    def __init__(
        self,
        obj: "Object",
        filename: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        """
        Represents object for uploading files from S3

        :param file: libcloud object in S3
        :param filename: Filename to be propagated to telegram.
        :param chunk_size: Uploading chunk size
        """
        super().__init__(filename=filename, chunk_size=chunk_size)

        self.obj = obj

    async def read(self, bot: "Bot") -> AsyncGenerator[bytes, None]:
        for chunk in self.obj.as_stream(self.chunk_size):
            yield chunk
