from typing import Literal

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import sqltypes

from djgram.configs import DB_SUPPORTS_ARRAYS
from djgram.db.models import TimeTrackableBaseModel


# pylint: disable=too-few-public-methods
class TelegramChat(TimeTrackableBaseModel):
    """
    This object represents a chat

    https://core.telegram.org/bots/api#chat
    """

    id: Mapped[int] = mapped_column(
        sqltypes.BigInteger,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True,
        doc=(
            "Unique identifier for this user or bot. This number may have more than "
            "32 significant bits and some programming languages may have "
            "difficulty/silent defects in interpreting it. But it has at most 52 "
            "significant bits, so a 64-bit integer or double-precision float type are "
            "safe for storing this identifier."
        ),
    )
    type: Mapped[Literal["private", "group", "supergroup", "channel"]] = mapped_column(
        sqltypes.String,
        doc="Type of chat, can be either “private”, “group”, “supergroup” or “channel”",
    )
    title: Mapped[str] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Title, for supergroups, channels and group chats",
    )
    username: Mapped[str] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Username, for private chats, supergroups and channels if available",
    )
    first_name: Mapped[str] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. First name of the other party in a private chat",
    )
    last_name: Mapped[str] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Last name of the other party in a private chat",
    )
    is_forum: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the supergroup chat is a forum (has topics enabled)",
    )
    # photo_id: Mapped[int] = mapped_column(
    #     sqlalchemy.ForeignKey(TelegramChatPhoto.id, ondelete="SET NULL"),
    #     nullable=True,
    #     doc="Optional. Chat photo. Returned only in getChat.",
    # )
    if DB_SUPPORTS_ARRAYS:
        active_usernames: Mapped[str] = mapped_column(
            sqltypes.ARRAY(sqltypes.String),
            nullable=True,
            doc="Optional. If non-empty, the list of all active chat usernames; "
            "for private chats, supergroups and channels. Returned only in getChat.",
        )
    emoji_status_custom_emoji_id: Mapped[str] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc=(
            "Optional. Custom emoji identifier of emoji status of the other party in a private chat. "
            "Returned only in getChat."
        ),
    )
    bio: Mapped[str] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Bio of the other party in a private chat. Returned only in getChat.",
    )
    has_private_forwards: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc=(
            "Optional. True, if privacy settings of the other party in the private chat "
            "allows to use tg://user?id=<user_id> links only in chats with the user. Returned only in getChat."
        ),
    )
    has_restricted_voice_and_video_messages: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc=(
            "Optional. True, if the privacy settings of the other party restrict sending voice and video note "
            "messages in the private chat. Returned only in getChat."
        ),
    )
    join_to_send_messages: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc=(
            "Optional. True, if users need to join the supergroup before they can send messages. "
            "Returned only in getChat."
        ),
    )
    join_by_request: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc=(
            "Optional. True, if all users directly joining the supergroup need to be approved "
            "by supergroup administrators. Returned only in getChat."
        ),
    )
    description: Mapped[str] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Description, for groups, supergroups and channel chats. Returned only in getChat.",
    )
    invite_link: Mapped[str] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Primary invite link, for groups, supergroups and channel chats. Returned only in getChat.",
    )
    # pinned_message = mapped_column(
    #     sqltypes.Message, nullable=True,
    #     doc="Optional. The most recent pinned message (by sending date). Returned only in getChat.")
    # permissions_id: Mapped[int] = mapped_column(
    #     sqlalchemy.ForeignKey(TelegramChatPermissions.id, ondelete="SET NULL"),
    #     nullable=True,
    #     doc="Optional. Default chat member permissions, for groups and supergroups. Returned only in getChat.",
    # )
    slow_mode_delay: Mapped[int] = mapped_column(
        sqltypes.BigInteger,
        nullable=True,
        doc=(
            "Optional. For supergroups, the minimum allowed delay between "
            "consecutive messages sent by each unpriviledged user; in seconds. Returned only in getChat."
        ),
    )
    message_auto_delete_time: Mapped[int] = mapped_column(
        sqltypes.BigInteger,
        nullable=True,
        doc=(
            "Optional. The time after which all messages sent to "
            "the chat will be automatically deleted; in seconds. Returned only in getChat."
        ),
    )
    unrestrict_boost_count: Mapped[int] = mapped_column(
        sqltypes.BigInteger,
        nullable=True,
        doc=(
            "	Optional. For supergroups, the minimum number of boosts that a non-administrator user "
            "needs to add in order to ignore slow mode and chat permissions. Returned only in getChat."
        ),
    )
    has_aggressive_anti_spam_enabled: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc=(
            "Optional. True, if aggressive anti-spam checks are enabled in the supergroup. "
            "The field is only available to chat administrators. Returned only in getChat."
        ),
    )
    has_hidden_members: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc=(
            "Optional. True, if non-administrators can only get the list of bots and administrators in the chat. "
            "Returned only in getChat."
        ),
    )
    has_protected_content: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if messages from the chat can't be forwarded to other chats. Returned only in getChat.",
    )
    sticker_set_name: Mapped[str] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. For supergroups, name of group sticker set. Returned only in getChat.",
    )
    can_set_sticker_set: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the bot can change the group sticker set. Returned only in getChat.",
    )
    custom_emoji_sticker_set_name: Mapped[str] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. For supergroups, the name of the group's custom emoji sticker set. "
        "Custom emoji from this set can be used by all users and bots in the group. Returned only in getChat.",
    )
    linked_chat_id: Mapped[int] = mapped_column(
        sqltypes.BigInteger,
        nullable=True,
        doc=(
            "Optional. Unique identifier for the linked chat, i.e. the discussion group identifier "
            "for a channel and vice versa; for supergroups and channel chats. "
            "This identifier may be greater than 32 bits and some programming languages may have "
            "difficulty/silent defects in interpreting it. But it is smaller than 52 bits, "
            "so a signed 64 bit integer or double-precision float type "
            "are safe for storing this identifier. Returned only in getChat."
        ),
    )
    # location_id: Mapped[int] = mapped_column(
    #     sqlalchemy.ForeignKey(TelegramChatLocation.id, ondelete="SET NULL"),
    #     nullable=True,
    #     doc="Optional. For supergroups, the location to which the supergroup is connected. Returned only in getChat.",
    # )
