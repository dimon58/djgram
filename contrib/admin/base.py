"""
Базовые классы для работы приложения администрирования
"""
import logging
import sys
from dataclasses import dataclass, field

from djgram.configs import ADMIN_ROWS_PER_PAGE

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class ModelAdmin:
    """
    Модель админки, как в django (не относится к базе данных на прямую)
    """

    model = None
    name: str = ""
    list_display: list[str] = []

    def __init_subclass__(cls, **kwargs):
        if cls.model is None:
            logger.critical(f"У {cls} не определена модель")
            sys.exit()

        if len(cls.list_display) == 0:
            logger.critical(f"У {cls} не заполнен list_display")
            sys.exit()

        if cls.name == "":
            logger.critical(f"У {cls} не заполнен name")
            sys.exit()


@dataclass
class AppAdmin:
    """
    Модель администрирования для приложения

    Attributes:
        verbose_name(str): Человекочитаемое название приложение
        admin_models(list[ModelAdmin]): Список всех административных панелей в приложении
    """

    verbose_name: str

    admin_models: list[type[ModelAdmin]] = field(default_factory=list)

    rows_per_page: int = ADMIN_ROWS_PER_PAGE

    def register(self, admin_model: type[ModelAdmin]):
        self.admin_models.append(admin_model)


apps_admins: list[AppAdmin] = []


def register_app_admin(app: AppAdmin):
    """
    Регистрирует админку для приложения
    """
    apps_admins.append(app)
    logger.info(f'Registered "{app.verbose_name}" admin')
