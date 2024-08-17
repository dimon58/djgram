from typing import Literal

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import sqltypes

from djgram.db.models import TimeTrackableBaseModel

from .misc import HasFullNameComponents


class AbstractTelegramChat(HasFullNameComponents, TimeTrackableBaseModel):
    """
    This object represents a common part of Chat and ChatFullInfo

    https://core.telegram.org/bots/api#chat
    https://core.telegram.org/bots/api#chatfullinfo
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        sqltypes.BigInteger,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for this chat. This number may have more than "
        "32 significant bits and some programming languages may have "
        "difficulty/silent defects in interpreting it. But it has at most 52 "
        "significant bits, so a signed 64-bit integer or double-precision float type are "
        "safe for storing this identifier.",
    )
    type: Mapped[Literal["private", "group", "supergroup", "channel"]] = mapped_column(
        sqltypes.String,
        doc="Type of the chat, can be either “private”, “group”, “supergroup” or “channel”",
    )
    title: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Title, for supergroups, channels and group chats",
    )
    username: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Username, for private chats, supergroups and channels if available",
    )
    first_name: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. First name of the other party in a private chat",
    )
    last_name: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Last name of the other party in a private chat",
    )
    is_forum: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the supergroup chat is a forum (has topics enabled)",
    )


# pylint: disable=too-few-public-methods
class TelegramChat(AbstractTelegramChat):
    """
    This object represents a chat

    https://core.telegram.org/bots/api#chat
    """

    def str_for_logging(self):
        return f"Telegram {self.type} chat [{self.id}]"
