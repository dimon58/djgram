"""
Приложение для администрирования


todo: Добавить отображение внешних ключей
todo: Сделать нормальное форматирование
"""

from .base import AppAdmin, ModelAdmin
from .handlers import router

__all__ = [
    "AppAdmin",
    "ModelAdmin",
    "router",
]
