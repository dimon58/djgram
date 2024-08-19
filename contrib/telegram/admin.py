"""
Администрирование
"""

from typing import Any

from aiogram.types import CallbackQuery

from djgram.contrib.admin import AppAdmin, ModelAdmin
from djgram.contrib.admin.action_buttons import AbstractObjectActionButton
from djgram.contrib.admin.rendering import OneLineTextRenderer, TelegramUsernameLinkRenderer
from djgram.system_configs import MIDDLEWARE_DB_SESSION_KEY

from .models import TelegramChat, TelegramChatFullInfo, TelegramUser

app = AppAdmin(verbose_name="Telegram")


# pylint: disable=too-few-public-methods
@app.register
class TelegramUserAdmin(ModelAdmin):
    """
    Админка для пользователей телеграмм
    """

    list_display = ("id", "username", "full_name")
    search_fields = ("id", "username", "first_name", "last_name", "language_code")
    model = TelegramUser
    name = "Пользователи телеграмм"
    show_docs = False
    widgets_override = {
        "first_name": OneLineTextRenderer,
        "last_name": OneLineTextRenderer,
        "username": TelegramUsernameLinkRenderer,
        "language_code": OneLineTextRenderer,
    }


# pylint: disable=too-few-public-methods
@app.register
class TelegramChatAdmin(ModelAdmin):
    """
    Админка для чатов телеграмм
    """

    list_display = ("id", "username", "full_name")
    search_fields = (
        "id",
        "type",
        "title",
        "username",
        "first_name",
        "last_name",
    )
    model = TelegramChat
    name = "Чаты телеграмм"
    show_docs = False
    widgets_override = {
        "type": OneLineTextRenderer,
        "title": OneLineTextRenderer,
        "username": TelegramUsernameLinkRenderer,
        "first_name": OneLineTextRenderer,
        "last_name": OneLineTextRenderer,
    }


class TelegramChatFullInfoUpdateObjectActionButton(AbstractObjectActionButton):
    """
    Кнопка обновления полной информации о чате через bot api
    """

    async def click(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, obj: TelegramChatFullInfo, callback_query: CallbackQuery, middleware_data: dict[str, Any]
    ) -> None:
        changed = await obj.update_from_telegram(callback_query.bot)  # pyright: ignore [reportArgumentType]
        await middleware_data[MIDDLEWARE_DB_SESSION_KEY].commit()

        msg_text = "обновлена" if changed else "уже актуальна"

        await callback_query.answer(f"Полная информация о чате {obj.id} {msg_text}")


# pylint: disable=too-few-public-methods
@app.register
class TelegramChatFullInfoAdmin(TelegramChatAdmin):
    """
    Админка для полной информации о чатах телеграмм
    """

    search_fields = (
        *TelegramChatAdmin.search_fields,
        "bio",
        "description",
    )
    model = TelegramChatFullInfo
    name = "Полная информация о чатах телеграмм"
    widgets_override = {
        **TelegramChatAdmin.widgets_override,
        "background_custom_emoji_id": OneLineTextRenderer,
        "profile_background_custom_emoji_id": OneLineTextRenderer,
        "emoji_status_custom_emoji_id": OneLineTextRenderer,
        "invite_link": OneLineTextRenderer,
        "sticker_set_name": OneLineTextRenderer,
        "custom_emoji_sticker_set_name": OneLineTextRenderer,
    }

    object_action_buttons = (
        TelegramChatFullInfoUpdateObjectActionButton("full_chat_info_update", "🔄 Обновить информацию"),
    )


# # pylint: disable=too-few-public-methods
# @app.register
# class TelegramLocationAdmin(ModelAdmin):
#     """
#     Админка для локаций телеграмм
#     """
#
#     list_display = ["longitude", "latitude", "heading"]
#     model = TelegramLocation
#     name = "Локации телеграмм"
#     show_docs = False
#
#
# # pylint: disable=too-few-public-methods
# @app.register
# class TelegramChatPhotoAdmin(ModelAdmin):
#     """
#     Админка для фотографий чатов телеграмм
#     """
#
#     list_display = ["id", "created_at"]
#     model = TelegramChatPhoto
#     name = "Фотографии чатов телеграмм"
#     show_docs = False
#
#
# # pylint: disable=too-few-public-methods
# @app.register
# class TelegramChatPermissionsAdmin(ModelAdmin):
#     """
#     Админка для разрешений чатов телеграмм
#     """
#
#     list_display = ["id", "created_at"]
#     model = TelegramChatPermissions
#     name = "Разрешения чатов телеграмм"
#     show_docs = False
#
#
# # pylint: disable=too-few-public-methods
# @app.register
# class TelegramChatLocationAdmin(ModelAdmin):
#     """
#     Админка для локаций чатов телеграмм
#     """
#
#     list_display = ["location_id", "address"]
#     model = TelegramChatLocation
#     name = "Локации чатов телеграмм"
#     show_docs = False
#
