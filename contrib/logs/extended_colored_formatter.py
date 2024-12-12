# pyright: reportGeneralTypeIssues=false
"""
Модуль для форматирования цветных логов
"""

import logging

from coloredlogs import ColoredFormatter, Empty
from humanfriendly.compat import coerce_string
from humanfriendly.terminal import ansi_wrap


class ExtendedColoredFormatter(ColoredFormatter):
    """
    Класс для форматирования цветных логов

    Форматирует цветом ещё и название уровня логов
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Apply level-specific styling to log records.
        Also colorize levelname.

        :param record: A :class:`~logging.LogRecord` object.
        :returns: The result of :func:`logging.Formatter.format()`.

        This method injects ANSI escape sequences that are specific to the
        level of each log record (because such logic cannot be expressed in the
        syntax of a log format string). It works by making a copy of the log
        record, changing the `msg` field inside the copy and passing the copy
        into the :func:`~logging.Formatter.format()` method of the base
        class.
        """
        style = self.nn.get(self.level_styles, record.levelname)
        # After the introduction of the `Empty' class it was reported in issue
        # 33 that format() can be called when `Empty' has already been garbage
        # collected. This explains the (otherwise rather out of place) `Empty
        # is not None' check in the following `if' statement. The reasoning
        # here is that it's much better to log a message without formatting
        # then to raise an exception ;-).
        #
        # For more details refer to issue 33 on GitHub:
        # https://github.com/xolox/python-coloredlogs/issues/33
        if style and Empty is not None:
            # Due to the way that Python's logging module is structured and
            # documented the only (IMHO) clean way to customize its behavior is
            # to change incoming LogRecord objects before they get to the base
            # formatter. However, we don't want to break other formatters and
            # handlers, so we copy the log record.
            #
            # In the past this used copy.copy() but as reported in issue 29
            # (which is reproducible) this can cause deadlocks. The following
            # Python voodoo is intended to accomplish the same thing as
            # copy.copy() without all the generalization and overhead that
            # we don't need for our -very limited-use case.
            #
            # For more details refer to issue 29 on GitHub:
            # https://github.com/xolox/python-coloredlogs/issues/29
            copy = Empty()
            copy.__class__ = record.__class__
            copy.__dict__.update(record.__dict__)
            copy.msg = ansi_wrap(coerce_string(record.msg), **style)  # pyright: ignore [reportAttributeAccessIssue]
            # Отличие
            copy.levelname = ansi_wrap(  # pyright: ignore [reportAttributeAccessIssue]
                coerce_string(record.levelname), **style
            )
            record = copy  # pyright: ignore [reportAssignmentType]

        # Delegate the remaining formatting to the base formatter.
        return logging.Formatter.format(self, record)
