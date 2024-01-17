"""
There is telegram types models
"""
from typing import Literal

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression, sqltypes

from djgram.configs import DB_SUPPORTS_ARRAYS
from djgram.db.models import TimeTrackableBaseModel


# pylint: disable=too-few-public-methods
class TelegramUser(TimeTrackableBaseModel):
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
        doc=(
            "Unique identifier for this user or bot. This number may have more than "
            "32 significant bits and some programming languages may have "
            "difficulty/silent defects in interpreting it. But it has at most 52 "
            "significant bits, so a 64-bit integer or double-precision float type are "
            "safe for storing this identifier."
        ),
    )

    is_bot: Mapped[bool] = mapped_column(sqltypes.Boolean, doc="True, if this user is a bot")

    first_name: Mapped[str] = mapped_column(sqltypes.String, doc="User's or bot's first name")
    last_name: Mapped[str] = mapped_column(sqltypes.String, nullable=True, doc="Optional. User's or bot's last name")
    username: Mapped[str] = mapped_column(sqltypes.String, nullable=True, doc="Optional. User's or bot's username")

    language_code: Mapped[str] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. IETF language tag of the user's language",
    )
    is_premium: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        default=False,
        nullable=True,
        server_default=expression.false(),
        doc="Optional. True, if this user is a Telegram Premium user",
    )
    added_to_attachment_menu: Mapped[str] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. True, if this user added the bot to the attachment menu",
    )
    can_join_groups: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the bot can be invited to groups. Returned only in getMe.",
    )
    can_read_all_group_messages: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if privacy mode is disabled for the bot. Returned only in getMe.",
    )
    supports_inline_queries: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the bot supports inline queries. Returned only in getMe.",
    )

    def get_full_name(self) -> str:
        """
        Возвращает полное имя пользователя.

        Оно получается конкатенацией first_name и last_name
        """

        if self.first_name is None:
            return self.last_name

        if self.last_name is None:
            return self.first_name

        return f"{self.first_name} {self.last_name}"

    def get_telegram_href_a_tag(self):
        """
        Возвращает ссылку на пользователя в виде поддерживаемого тега для сообщения телеграмм

        https://core.telegram.org/bots/api#html-style
        """
        return f'<a href="tg://user?id={self.id}">{self.get_full_name()}</a>'


# pylint: disable=too-few-public-methods
class TelegramLocation(TimeTrackableBaseModel):
    """
    This object represents a point on the map

    https://core.telegram.org/bots/api#location
    """

    longitude: Mapped[float] = mapped_column(sqltypes.Float, doc="Longitude as defined by sender")
    latitude: Mapped[float] = mapped_column(sqltypes.Float, doc="Latitude as defined by sender")
    horizontal_accuracy: Mapped[float] = mapped_column(
        sqltypes.Float,
        nullable=True,
        doc="Optional. The radius of uncertainty for the location, measured in meters; 0-1500",
    )
    live_period: Mapped[int] = mapped_column(
        sqltypes.BigInteger,
        nullable=True,
        doc=(
            "Optional. Time relative to the message sending date, during which "
            "the location can be updated; in seconds. For active live locations only."
        ),
    )
    heading: Mapped[int] = mapped_column(
        sqltypes.BigInteger,
        nullable=True,
        doc="Optional. The direction in which user is moving, in degrees; 1-360. For active live locations only.",
    )
    proximity_alert_radius: Mapped[int] = mapped_column(
        sqltypes.BigInteger,
        nullable=True,
        doc=(
            "Optional. Maximum distance for proximity alerts about "
            "approaching another chat member, in meters. For sent live locations only."
        ),
    )


# pylint: disable=too-few-public-methods
class TelegramChatPhoto(TimeTrackableBaseModel):
    """
    This object represents a chat photo

    https://core.telegram.org/bots/api#chatphoto
    """

    small_file_id: Mapped[str] = mapped_column(
        sqltypes.String,
        doc=(
            "File identifier of small (160x160) chat photo. This file_id can be used only for photo "
            "download and only for as long as the photo is not changed."
        ),
    )
    small_file_unique_id: Mapped[str] = mapped_column(
        sqltypes.String,
        doc=(
            "Unique file identifier of small (160x160) chat photo, which is supposed to be the "
            "same over time and for different bots. Can't be used to download or reuse the file."
        ),
    )
    big_file_id: Mapped[str] = mapped_column(
        sqltypes.String,
        doc=(
            "File identifier of big (640x640) chat photo. This file_id can be used only for photo "
            "download and only for as long as the photo is not changed."
        ),
    )
    big_file_unique_id: Mapped[str] = mapped_column(
        sqltypes.String,
        doc=(
            "Unique file identifier of big (640x640) chat photo, which is supposed to be the "
            "same over time and for different bots. Can't be used to download or reuse the file."
        ),
    )


# pylint: disable=too-few-public-methods
class TelegramChatPermissions(TimeTrackableBaseModel):
    """
    Describes actions that a non-administrator user is allowed to take in a chat

    https://core.telegram.org/bots/api#chatpermissions
    """

    can_send_messages: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the user is allowed to send text messages, contacts, invoices, locations and venues",
    )
    can_send_audios: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the user is allowed to send audios",
    )
    can_send_documents: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the user is allowed to send documents",
    )
    can_send_photos: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the user is allowed to send photos",
    )
    can_send_videos: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the user is allowed to send videos",
    )
    can_send_video_notes: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the user is allowed to send video notes",
    )
    can_send_voice_notes: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the user is allowed to send voice notes",
    )
    can_send_polls: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the user is allowed to send polls",
    )
    can_send_other_messages: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the user is allowed to send animations, games, stickers and use inline bots",
    )
    can_add_web_page_previews: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the user is allowed to add web page previews to their messages",
    )
    can_change_info: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc=(
            "Optional. True, if the user is allowed to change the chat title, photo and other settings. "
            "Ignored in public supergroups"
        ),
    )
    can_invite_users: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the user is allowed to invite new users to the chat",
    )
    can_pin_messages: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the user is allowed to pin messages. Ignored in public supergroups",
    )
    can_manage_topics: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc=(
            "Optional. True, if the user is allowed to create forum topics. "
            "If omitted defaults to the value of can_pin_messages"
        ),
    )


# pylint: disable=too-few-public-methods
class TelegramChatLocation(TimeTrackableBaseModel):
    """
    Represents a location to which a chat is connected

    https://core.telegram.org/bots/api#chatlocation
    """

    location_id: Mapped[int] = mapped_column(
        sqlalchemy.ForeignKey(TelegramLocation.id, ondelete="SET NULL"),
        doc="The location to which the supergroup is connected. Can't be a live location.",
    )
    address: Mapped[str] = mapped_column(
        sqltypes.String,
        doc="Location address; 1-64 characters, as defined by the chat owner",
    )


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
    photo_id: Mapped[int] = mapped_column(
        sqlalchemy.ForeignKey(TelegramChatPhoto.id, ondelete="SET NULL"),
        nullable=True,
        doc="Optional. Chat photo. Returned only in getChat.",
    )
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
    permissions_id: Mapped[int] = mapped_column(
        sqlalchemy.ForeignKey(TelegramChatPermissions.id, ondelete="SET NULL"),
        nullable=True,
        doc="Optional. Default chat member permissions, for groups and supergroups. Returned only in getChat.",
    )
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
    location_id: Mapped[int] = mapped_column(
        sqlalchemy.ForeignKey(TelegramChatLocation.id, ondelete="SET NULL"),
        nullable=True,
        doc="Optional. For supergroups, the location to which the supergroup is connected. Returned only in getChat.",
    )
