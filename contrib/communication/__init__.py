"""
Приложение для коммуникации с пользователями

Позволяет:
- Делать массовую рассылку


Для работы требует установленные DbSessionMiddleware, TelegramMiddleware, AuthMiddleware
"""

from .handlers import router

__all__ = [
    "router",
]
