import logging
from datetime import UTC, datetime

import aiogram
from aiogram import Bot
from djgram.configs import DB_SUPPORTS_ARRAYS
from djgram.db.pydantic_field import ImmutablePydanticField, PydanticField
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import sqltypes

from .chat import AbstractTelegramChat

logger = logging.getLogger(__name__)


class TelegramChatFullInfo(AbstractTelegramChat):
    """
    This object contains full information about a chat

    https://core.telegram.org/bots/api#chatfullinfo
    """

    accent_color_id: Mapped[int] = mapped_column(
        sqltypes.Integer,
        doc="Identifier of the accent color for the chat name and backgrounds "
        "of the chat photo, reply header, and link preview. "
        "See accent colors https://core.telegram.org/bots/api#accent-colors for more details.",
    )

    max_reaction_count: Mapped[int] = mapped_column(
        sqltypes.Integer,
        doc="The maximum number of reactions that can be set on a message in the chat",
    )

    photo: Mapped[aiogram.types.ChatPhoto | None] = mapped_column(
        ImmutablePydanticField(aiogram.types.ChatPhoto),
        nullable=True,
        doc="Optional. Chat photo",
    )

    if DB_SUPPORTS_ARRAYS:
        active_usernames: Mapped[list[str] | None] = mapped_column(
            sqltypes.ARRAY(sqltypes.String),
            nullable=True,
            doc="Optional. If non-empty, the list of all active chat usernames; "
            "for private chats, supergroups and channels",
        )

    birthdate: Mapped[aiogram.types.Birthdate | None] = mapped_column(
        ImmutablePydanticField(aiogram.types.Birthdate),
        nullable=True,
        doc="Optional. For private chats, the date of birth of the user",
    )

    business_intro: Mapped[aiogram.types.BusinessIntro | None] = mapped_column(
        ImmutablePydanticField(aiogram.types.BusinessIntro),
        nullable=True,
        doc="Optional. For private chats with business accounts, the intro of the business",
    )

    business_location: Mapped[aiogram.types.BusinessLocation | None] = mapped_column(
        ImmutablePydanticField(aiogram.types.BusinessLocation),
        nullable=True,
        doc="Optional. For private chats with business accounts, the location of the business",
    )

    business_opening_hours: Mapped[aiogram.types.BusinessOpeningHours | None] = mapped_column(
        ImmutablePydanticField(aiogram.types.BusinessOpeningHours),
        nullable=True,
        doc="Optional. For private chats with business accounts, the opening hours of the business",
    )

    # TODO: сделать внешний ключ на модель чата
    personal_chat: Mapped[aiogram.types.Chat | None] = mapped_column(
        ImmutablePydanticField(aiogram.types.Chat),
        nullable=True,
        doc="Optional. For private chats, the personal channel of the user",
    )

    if DB_SUPPORTS_ARRAYS:
        available_reactions: Mapped[list[aiogram.types.ReactionType] | None] = mapped_column(
            sqltypes.ARRAY(ImmutablePydanticField(aiogram.types.ReactionType)),
            nullable=True,
            doc="Optional. List of available reactions allowed in the chat. "
            "If omitted, then all emoji reactions are allowed.",
        )

    background_custom_emoji_id: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Custom emoji identifier of the emoji chosen by the chat "
        "for the reply header and link preview background",
    )

    profile_accent_color_id: Mapped[int | None] = mapped_column(
        sqltypes.Integer,
        nullable=True,
        doc="Optional. Identifier of the accent color for the chat's profile background. "
        "See profile accent colors for more details.",
    )

    profile_background_custom_emoji_id: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Custom emoji identifier of the emoji chosen by the chat for its profile background",
    )

    emoji_status_custom_emoji_id: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Custom emoji identifier of the emoji status of the chat or the other party in a private chat",
    )

    emoji_status_expiration_date: Mapped[datetime | None] = mapped_column(
        sqltypes.DateTime(timezone=True),
        nullable=True,
        doc="Optional. Expiration date of the emoji status of the chat or the other party "
        "in a private chat, in Unix time, if any",
    )

    bio: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Bio of the other party in a private chat",
    )

    has_private_forwards: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if privacy settings of the other party in the private chat "
        "allows to use tg://user?id=<user_id> links only in chats with the user",
    )

    has_restricted_voice_and_video_messages: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the privacy settings of the other party restrict "
        "sending voice and video note messages in the private chat",
    )

    join_to_send_messages: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if users need to join the supergroup before they can send messages",
    )

    join_by_request: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if all users directly joining the supergroup "
        "without using an invite link need to be approved by supergroup administrators",
    )

    description: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Description, for groups, supergroups and channel chats",
    )

    invite_link: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. Primary invite link, for groups, supergroups and channel chats",
    )

    pinned_message: Mapped[aiogram.types.Message | None] = mapped_column(
        ImmutablePydanticField(aiogram.types.Message),
        nullable=True,
        doc="Optional. The most recent pinned message (by sending date)",
    )

    permissions: Mapped[aiogram.types.ChatPermissions | None] = mapped_column(
        PydanticField(aiogram.types.ChatPermissions),
        nullable=True,
        doc="Optional. Default chat member permissions, for groups and supergroups",
    )

    can_send_gift: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if gifts can be sent to the chat.",
    )

    can_send_paid_media: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if paid media messages can be sent or forwarded to the channel chat. "
        "The field is available only for channel chats.",
    )

    slow_mode_delay: Mapped[int | None] = mapped_column(
        sqltypes.Integer,
        nullable=True,
        doc="Optional. For supergroups, the minimum allowed delay between consecutive messages "
        "sent by each unprivileged user; in seconds",
    )

    unrestrict_boost_count: Mapped[int | None] = mapped_column(
        sqltypes.Integer,
        nullable=True,
        doc="Optional. For supergroups, the minimum number of boosts that "
        "a non-administrator user needs to add in order to ignore slow mode and chat permissions",
    )

    message_auto_delete_time: Mapped[int | None] = mapped_column(
        sqltypes.Integer,
        nullable=True,
        doc="Optional. The time after which all messages sent to the chat will be automatically deleted; in seconds",
    )

    has_aggressive_anti_spam_enabled: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if aggressive anti-spam checks are enabled in the supergroup. "
        "The field is only available to chat administrators.",
    )

    has_hidden_members: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if non-administrators can only get the list of bots and administrators in the chat",
    )

    has_protected_content: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if messages from the chat can't be forwarded to other chats",
    )

    has_visible_history: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if new chat members will have access to old messages; "
        "available only to chat administrators",
    )

    sticker_set_name: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. For supergroups, name of the group sticker set",
    )

    can_set_sticker_set: Mapped[bool | None] = mapped_column(
        sqltypes.Boolean,
        nullable=True,
        doc="Optional. True, if the bot can change the group sticker set",
    )

    custom_emoji_sticker_set_name: Mapped[str | None] = mapped_column(
        sqltypes.String,
        nullable=True,
        doc="Optional. For supergroups, the name of the group's custom emoji sticker set. "
        "Custom emoji from this set can be used by all users and bots in the group.",
    )

    linked_chat_id: Mapped[int | None] = mapped_column(
        sqltypes.BigInteger,
        nullable=True,
        doc="Optional. Unique identifier for the linked chat, i.e. the discussion group identifier "
        "for a channel and vice versa; "
        "for supergroups and channel chats. This identifier may be greater than "
        "32 bits and some programming languages may have difficulty/silent defects in interpreting it. "
        "But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float type "
        "are safe for storing this identifier.",
    )

    location: Mapped[aiogram.types.ChatLocation | None] = mapped_column(
        ImmutablePydanticField(aiogram.types.ChatLocation),
        nullable=True,
        doc="Optional. For supergroups, the location to which the supergroup is connected",
    )

    def str_for_logging(self) -> str:
        return f"Telegram {self.type} chat full info [{self.id}]"

    async def update_from_telegram(self, bot: Bot, request_timeout: int | None = None) -> bool:
        """
        Запрашивает информацию о чате через bot api.
        Если что-то отличается от того, что храниться в базе данных, то устанавливает новые значения.
        Также устанавливает поле update_at на текущее время.

        Возвращает True, если были какие-то изменения, кроме update_at
        """

        logger.info("Updating chat full info %s", self.id)
        updated = await bot.get_chat(self.id, request_timeout)

        changed = False
        for field_name in updated.model_fields:
            value = getattr(updated, field_name)
            if getattr(self, field_name) != value:
                setattr(self, field_name, value)
                changed = True

        if changed:
            logger.info("Updated %s", self.str_for_logging())

        self.updated_at = datetime.now(tz=UTC)

        return changed
