"""
Администрирование
"""

from djgram.contrib.admin import AppAdmin, ModelAdmin
from djgram.contrib.admin.rendering import AdminFieldRenderer, TelegramUsernameLinkRenderer

from .models import User

app = AppAdmin(verbose_name="Пользователи")


@app.register
class UserAdmin(ModelAdmin):
    list_display = ["id", "telegram_user__username", "telegram_user__full_name"]
    model = User
    name = "Пользователи"

    @classmethod
    def get_fields_of_model(cls) -> list[AdminFieldRenderer]:
        return [
            *super().get_fields_of_model(),
            TelegramUsernameLinkRenderer("telegram_user__username", "username"),
        ]
