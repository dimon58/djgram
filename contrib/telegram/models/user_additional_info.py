from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import sqltypes


# pylint: disable=too-few-public-methods
class TelegramUserAdditionalInfo:
    """
    This object represents a additional info for Telegram user or bot

    This info returned only in getMe

    https://core.telegram.org/bots/api#getme
    https://core.telegram.org/bots/api#user
    """

    can_join_groups: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        doc="Optional. True, if the bot can be invited to groups. Returned only in getMe.",
    )
    can_read_all_group_messages: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        doc="Optional. True, if privacy mode is disabled for the bot. Returned only in getMe.",
    )
    supports_inline_queries: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        doc="Optional. True, if the bot supports inline queries. Returned only in getMe.",
    )
    can_connect_to_business: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        doc="Optional. True, if the bot can be connected to a Telegram Business account to receive its messages. "
        "Returned only in getMe.",
    )
    has_main_web_app: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        doc="Optional. True, if the bot has a main Web App. Returned only in getMe.",
    )
