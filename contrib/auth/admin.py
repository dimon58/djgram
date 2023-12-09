"""
Администрирование
"""
from djgram.contrib.admin import AppAdmin, ModelAdmin

from .models import User

app = AppAdmin(verbose_name="Пользователи")


@app.register
class UserAdmin(ModelAdmin):
    list_display = ["id", "telegram_user__username"]
    model = User
    name = "Пользователи"
