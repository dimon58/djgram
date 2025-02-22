import contextvars
import logging

UPDATE_ID: contextvars.ContextVar[int | None] = contextvars.ContextVar("UPDATE_ID", default=None)


class UpdateIdContextFilter(logging.Filter):
    """
    Записывает в контекст логгера update_id
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.update_id = UPDATE_ID.get()
        return True
