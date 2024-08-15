"""
Администрирование
"""

from djgram.contrib.admin import AppAdmin, ModelAdmin

from .models import TelegramChat, TelegramUser

app = AppAdmin(verbose_name="Telegram")


# pylint: disable=too-few-public-methods
@app.register
class TelegramUserAdmin(ModelAdmin):
    """
    Админка для пользователей телеграмм
    """

    list_display = ["id", "username", "first_name", "last_name"]
    search_fields = ["id", "username", "first_name", "last_name", "language_code"]
    model = TelegramUser
    name = "Пользователи телеграмм"
    show_docs = False


# pylint: disable=too-few-public-methods
@app.register
class TelegramChatAdmin(ModelAdmin):
    """
    Админка для чатов телеграмм
    """

    list_display = ["id", "username", "first_name", "last_name"]
    search_fields = [
        "id",
        "type",
        "title",
        "username",
        "first_name",
        "last_name",
    ]
    model = TelegramChat
    name = "Чаты телеграмм"
    show_docs = False


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
