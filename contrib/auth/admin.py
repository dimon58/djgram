"""
Администрирование
"""

import logging
from typing import Any

from aiogram.types import CallbackQuery
from djgram.contrib.admin import AppAdmin, ModelAdmin
from djgram.contrib.admin.action_buttons import AbstractObjectActionButton
from djgram.contrib.admin.misc import get_admin_representation_for_logging_from_middleware_data
from djgram.contrib.admin.rendering import AdminFieldRenderer, TelegramUsernameLinkRenderer
from djgram.system_configs import MIDDLEWARE_DB_SESSION_KEY

from .models import User

logger = logging.getLogger(__name__)

app = AppAdmin(verbose_name="Пользователи")


class BanUserButton(AbstractObjectActionButton[User]):
    def get_title(self, obj: User) -> str:
        return "🔒 Забанить" if not obj.banned else "🔑 Разбанить"

    async def click(self, obj: User, callback_query: CallbackQuery, middleware_data: dict[str, Any]) -> None:
        obj.banned = not obj.banned
        await middleware_data[MIDDLEWARE_DB_SESSION_KEY].commit()

        logger.info(
            "Admin %s %sbanned user %s (%s)",
            get_admin_representation_for_logging_from_middleware_data(middleware_data),
            "" if obj.banned else "un",
            obj.id,
            obj.telegram_user.str_for_logging(),
        )


class ToggleAdminUserButton(AbstractObjectActionButton[User]):
    def get_title(self, obj: User) -> str:
        return "⭐ Сделать администратором" if not obj.is_admin else "👤 Исключить из администраторов"

    async def click(self, obj: User, callback_query: CallbackQuery, middleware_data: dict[str, Any]) -> None:
        obj.is_admin = not obj.is_admin
        await middleware_data[MIDDLEWARE_DB_SESSION_KEY].commit()

        if obj.is_admin:
            logger.info(
                "Admin %s made user %s (%s) the administrator",
                get_admin_representation_for_logging_from_middleware_data(middleware_data),
                obj.id,
                obj.telegram_user.str_for_logging(),
            )
        else:
            logger.info(
                "Admin %s excluded user %s (%s) from the administrators",
                get_admin_representation_for_logging_from_middleware_data(middleware_data),
                obj.id,
                obj.telegram_user.str_for_logging(),
            )


@app.register
class UserAdmin(ModelAdmin):
    list_display = ("id", "telegram_user__username", "telegram_user__full_name")
    model = User
    name = "Пользователи"

    object_action_buttons = (
        BanUserButton("toggle_ban_user", "Toggle ban"),
        ToggleAdminUserButton("toggle_admin_user", "Toggle admin"),
    )

    @classmethod
    def get_fields_widgets(cls) -> list[AdminFieldRenderer]:
        return [
            *super().get_fields_widgets(),
            TelegramUsernameLinkRenderer("telegram_user__username", "username"),
        ]
