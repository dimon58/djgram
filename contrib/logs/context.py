import contextvars
import logging

UPDATE_ID = contextvars.ContextVar("UPDATE_ID", default=None)


class UpdateIdContextFilter(logging.Filter):
    """
    Записывает в контекст логгера update_id
    """

    def filter(self, record):
        record.update_id = UPDATE_ID.get()
        return True
