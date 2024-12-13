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

HasFile: TypeAlias = Audio | Animation | Document | PhotoSize | Sticker | Video | VideoNote | Voice
HasMimeType: TypeAlias = Audio | Animation | Document | Video | Voice
HasFileName: TypeAlias = Audio | Animation | Document | Video


def get_file_content(message: Message) -> HasFile | None:  # noqa: C901, PLR0911
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


def convert_accepted_files(accepted_files: str | list[str]) -> list[str]:
    """
    Convert accepted_files to a list if it's a string
    """
    if isinstance(accepted_files, str):
        return [item.strip() for item in accepted_files.split(",")]

    return [item.strip().lower().lower() for item in accepted_files]


def check_accept(file_name: str, mime_type: str, accepted_files: str | list[str]) -> bool:
    """
    Check if the provided file type should be accepted by the input with accept attribute.

    https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/accept

    Based on https://github.com/react-dropzone/attr-accept/blob/main/src/index.js

    Args:
        file_name: file name
        mime_type: file mime type
        accepted_files (str or List[str]): A string of comma-separated file types or a list of file types.

    Returns:
        bool: True if the file is accepted, False otherwise.
    """

    accepted_files_array = convert_accepted_files(accepted_files)
    if len(accepted_files_array) == 0:
        return True

    file_name = file_name.lower()
    mime_type = mime_type.lower()
    base_mime_type = mime_type.split("/")[0]

    for valid_type in accepted_files_array:
        if valid_type.startswith("."):
            # Check for file extensions
            if file_name.endswith(valid_type):
                return True
        elif valid_type.endswith("/*"):
            # Check for base mime type
            if base_mime_type == valid_type.split("/")[0]:
                return True
        elif mime_type == valid_type:
            # Exact mime type match
            return True

    return False
