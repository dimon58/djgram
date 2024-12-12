from typing import TypeAlias

from aiogram.types import (
    Animation,
    Audio,
    Document,
    Message,
    PhotoSize,
    Sticker,
    Video,
    VideoNote,
    Voice,
)

ContainsFile: TypeAlias = Audio | Animation | Document | PhotoSize | Sticker | Video | VideoNote | Voice


def get_file_content(message: Message) -> ContainsFile | None:  # noqa: C901, PLR0911
    """
    Возвращают файл из сообщения, если он там есть, иначе None
    """
    if message.audio:
        return message.audio
    if message.animation:
        return message.animation
    if message.document:
        return message.document
    if message.photo:
        return message.photo[-1]
    if message.sticker:
        return message.sticker
    if message.video:
        return message.video
    if message.video_note:
        return message.video_note
    if message.voice:
        return message.voice
    if message.new_chat_photo:
        return message.new_chat_photo[-1]

    return None
