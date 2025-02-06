"""
Диалоги:

Просмотр записей в базе данных
"""

from .dialogs import admin_dialog
from .states import AdminStates

__all__ = [
    "AdminStates",
    "admin_dialog",
]
