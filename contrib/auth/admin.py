"""
Администрирование
"""

from djgram.contrib.admin import AppAdmin, ModelAdmin

from .models import User

app = AppAdmin(verbose_name="Пользователи")


@app.register
class UserAdmin(ModelAdmin):
    list_display = ["id", "telegram_user__username", "telegram_user__full_name"]
    model = User
    name = "Пользователи"
