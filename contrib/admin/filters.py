"""
Фильтры, пропускающие запросы только от администраторов
"""

from aiogram import F, Router
from aiogram.filters import MagicData


def make_admin_router(parent_router: Router | None = None) -> Router:
    """
    Создает роутер, доступ к которому имеют только администраторы.

    Если передан parent_router, то создается роутер, включенный в parent_router
    """
    _filter = MagicData(F.user.is_admin.is_(True))

    nested_admin_router = Router()

    nested_admin_router.message.filter(_filter)
    nested_admin_router.callback_query.filter(_filter)

    if parent_router is not None:
        parent_router.include_router(nested_admin_router)

    return nested_admin_router
