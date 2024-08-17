class HasFullNameComponents:
    """
    Представляет модель, содержащую поля first_name и last_name

    Например TelegramChat, TelegramChatFullInfo, TelegramUser
    """

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

    @property
    def full_name(self):
        return self.get_full_name()


# pylint: disable=too-few-public-methods
# class TelegramLocation(TimeTrackableBaseModel):
#     """
#     This object represents a point on the map
#
#     https://core.telegram.org/bots/api#location
#     """
#
#     longitude: Mapped[float] = mapped_column(sqltypes.Float, doc="Longitude as defined by sender")
#     latitude: Mapped[float] = mapped_column(sqltypes.Float, doc="Latitude as defined by sender")
#     horizontal_accuracy: Mapped[float] = mapped_column(
#         sqltypes.Float,
#         nullable=True,
#         doc="Optional. The radius of uncertainty for the location, measured in meters; 0-1500",
#     )
#     live_period: Mapped[int] = mapped_column(
#         sqltypes.BigInteger,
#         nullable=True,
#         doc=(
#             "Optional. Time relative to the message sending date, during which "
#             "the location can be updated; in seconds. For active live locations only."
#         ),
#     )
#     heading: Mapped[int] = mapped_column(
#         sqltypes.BigInteger,
#         nullable=True,
#         doc="Optional. The direction in which user is moving, in degrees; 1-360. For active live locations only.",
#     )
#     proximity_alert_radius: Mapped[int] = mapped_column(
#         sqltypes.BigInteger,
#         nullable=True,
#         doc=(
#             "Optional. Maximum distance for proximity alerts about "
#             "approaching another chat member, in meters. For sent live locations only."
#         ),
#     )


# pylint: disable=too-few-public-methods
# class TelegramChatPhoto(TimeTrackableBaseModel):
#     """
#     This object represents a chat photo
#
#     https://core.telegram.org/bots/api#chatphoto
#     """
#
#     small_file_id: Mapped[str] = mapped_column(
#         sqltypes.String,
#         doc=(
#             "File identifier of small (160x160) chat photo. This file_id can be used only for photo "
#             "download and only for as long as the photo is not changed."
#         ),
#     )
#     small_file_unique_id: Mapped[str] = mapped_column(
#         sqltypes.String,
#         doc=(
#             "Unique file identifier of small (160x160) chat photo, which is supposed to be the "
#             "same over time and for different bots. Can't be used to download or reuse the file."
#         ),
#     )
#     big_file_id: Mapped[str] = mapped_column(
#         sqltypes.String,
#         doc=(
#             "File identifier of big (640x640) chat photo. This file_id can be used only for photo "
#             "download and only for as long as the photo is not changed."
#         ),
#     )
#     big_file_unique_id: Mapped[str] = mapped_column(
#         sqltypes.String,
#         doc=(
#             "Unique file identifier of big (640x640) chat photo, which is supposed to be the "
#             "same over time and for different bots. Can't be used to download or reuse the file."
#         ),
#     )


# pylint: disable=too-few-public-methods
# class TelegramChatPermissions(TimeTrackableBaseModel):
#     """
#     Describes actions that a non-administrator user is allowed to take in a chat
#
#     https://core.telegram.org/bots/api#chatpermissions
#     """
#
#     can_send_messages: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc="Optional. True, if the user is allowed to send text messages, contacts, invoices, locations and venues",
#     )
#     can_send_audios: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc="Optional. True, if the user is allowed to send audios",
#     )
#     can_send_documents: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc="Optional. True, if the user is allowed to send documents",
#     )
#     can_send_photos: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc="Optional. True, if the user is allowed to send photos",
#     )
#     can_send_videos: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc="Optional. True, if the user is allowed to send videos",
#     )
#     can_send_video_notes: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc="Optional. True, if the user is allowed to send video notes",
#     )
#     can_send_voice_notes: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc="Optional. True, if the user is allowed to send voice notes",
#     )
#     can_send_polls: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc="Optional. True, if the user is allowed to send polls",
#     )
#     can_send_other_messages: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc="Optional. True, if the user is allowed to send animations, games, stickers and use inline bots",
#     )
#     can_add_web_page_previews: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc="Optional. True, if the user is allowed to add web page previews to their messages",
#     )
#     can_change_info: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc=(
#             "Optional. True, if the user is allowed to change the chat title, photo and other settings. "
#             "Ignored in public supergroups"
#         ),
#     )
#     can_invite_users: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc="Optional. True, if the user is allowed to invite new users to the chat",
#     )
#     can_pin_messages: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc="Optional. True, if the user is allowed to pin messages. Ignored in public supergroups",
#     )
#     can_manage_topics: Mapped[bool] = mapped_column(
#         sqltypes.Boolean,
#         nullable=True,
#         doc=(
#             "Optional. True, if the user is allowed to create forum topics. "
#             "If omitted defaults to the value of can_pin_messages"
#         ),
#     )


# pylint: disable=too-few-public-methods
# class TelegramChatLocation(TimeTrackableBaseModel):
#     """
#     Represents a location to which a chat is connected
#
#     https://core.telegram.org/bots/api#chatlocation
#     """
#
#     location_id: Mapped[int] = mapped_column(
#         sqlalchemy.ForeignKey(TelegramLocation.id, ondelete="SET NULL"),
#         doc="The location to which the supergroup is connected. Can't be a live location.",
#     )
#     address: Mapped[str] = mapped_column(
#         sqltypes.String,
#         doc="Location address; 1-64 characters, as defined by the chat owner",
#     )
