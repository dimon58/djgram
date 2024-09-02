from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression, sqltypes

from djgram.db.models import TimeTrackableBaseModel

from .misc import HasFullNameComponents


# pylint: disable=too-few-public-methods
class TelegramUser(HasFullNameComponents, TimeTrackableBaseModel):
    """
    This object represents a Telegram user or bot

    https://core.telegram.org/bots/api#user
    """

    id: Mapped[int] = mapped_column(
        sqltypes.BigInteger,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for this user or bot. This number may have more than "
        "32 significant bits and some programming languages may have "
        "difficulty/silent defects in interpreting it. But it has at most 52 "
        "significant bits, so a 64-bit integer or double-precision float type are "
        "safe for storing this identifier.",
    )

    is_bot: Mapped[bool] = mapped_column(sqltypes.Boolean, doc="True, if this user is a bot")

    first_name: Mapped[str] = mapped_column(sqltypes.String, doc="User's or bot's first name")
    last_name: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. User's or bot's last name",
    )
    username: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. User's or bot's username",
    )

    language_code: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. IETF language tag of the user's language",
    )
    is_premium: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        default=False,
        server_default=expression.false(),
        doc="Optional. True, if this user is a Telegram Premium user",
    )
    added_to_attachment_menu: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        default=False,
        server_default=expression.false(),
        doc="Optional. True, if this user added the bot to the attachment menu",
    )

    def get_telegram_href_a_tag(self) -> str:
        """
        Возвращает ссылку на пользователя в виде поддерживаемого тега для сообщения телеграмм

        https://core.telegram.org/bots/api#html-style
        """
        return f'<a href="tg://user?id={self.id}">{self.get_full_name()}</a>'

    def get_markdown_link(self) -> str:
        """
        Возвращает ссылку на пользователя в виде поддерживаемого тега для сообщения телеграмм

        https://core.telegram.org/bots/api#html-style
        """
        return f"[{self.get_full_name()}](tg://user?id={self.id})"

    def str_for_logging(self) -> str:
        return f"Telegram user [{self.id}] {self.full_name}"
