import asyncio
from logging import Formatter, LogRecord, StreamHandler

from aiogram import Bot
from aiogram.types import BufferedInputFile

from djgram.utils import resolve_pyobj


class TelegramFormatter(Formatter):
    """
    Форматирует сообщение без стектрейса,
    разделяет новой строкой метаинформацию и сообщение
    """

    def format(self, record):
        """
        Format the specified record as text.

        The record's attribute dictionary is used as the operand to a
        string formatting operation which yields the returned string.
        Before formatting the dictionary, a couple of preparatory steps
        are carried out. The message attribute of the record is computed
        using LogRecord.getMessage(). If the formatting string uses the
        time (as determined by a call to usesTime(), formatTime() is
        called to format the event time. If there is exception information,
        it is formatted using formatException() and appended to the message.
        """
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        # Добавляем перенос строки к сообщению
        record.message = "\n" + record.message
        formatted_message = self.formatMessage(record)
        # Удаляем этот перенос строки
        record.message = record.message[1:]

        return formatted_message


class TelegramHandler(StreamHandler):
    """
    Sends logs to telegram
    """

    def __init__(self, token: str, chat_ids_getter: str, timeout: int = 10):
        """
        Args:
            token: telegram bot token
            chat_ids_getter: путь до функции, которое возвращает список id чатов для отправки сообщений
            timeout: seconds for retrying to send log if error occupied
        """

        super().__init__()
        self.timeout = timeout
        self.bot = Bot(token=token)
        self.loop = asyncio.get_event_loop()
        self.chat_ids_getter = resolve_pyobj(chat_ids_getter)

    def emit(self, record: LogRecord) -> None:
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            if record.exc_text:
                traceback_file = BufferedInputFile(record.exc_text.encode("utf-8"), "traceback.txt")
            else:
                traceback_file = None

            coros = []

            for chat_id in self.chat_ids_getter():
                if record.exc_text:
                    coro = self.bot.send_document(
                        chat_id=chat_id,
                        document=traceback_file,
                        caption=msg,
                    )
                else:
                    coro = self.bot.send_message(chat_id, msg)

                coros.append(coro)

            if len(coros) == 0:
                return

            asyncio.gather(*coros)

        except RecursionError:
            raise

        except Exception:  # noqa: BLE001
            self.handleError(record)
