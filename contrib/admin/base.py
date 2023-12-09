"""
Базовые классы для работы приложения администрирования
"""
import logging
import sys
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from djgram.configs import ADMIN_ROWS_PER_PAGE
from djgram.db.models import Base

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class ModelAdmin:
    """
    Модель админки, как в django (не относится к базе данных на прямую)
    """

    model: type[Base] = None  # Модель
    name: str = ""  # Название
    list_display: list[str] = []  # Список колонок для показа при предпросмотре
    show_count: bool = True  # Показывать число записей
    show_docs: bool = True  # Показывать документацию, если есть

    skip_synonyms_origin: bool = True  # Не показывать поля, для которых есть синонимы

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

    @classmethod
    async def display_name(cls, db_session: AsyncSession) -> str:
        if cls.show_count:
            count_stmt = select(func.count("*")).select_from(cls.model)
            count = await db_session.scalar(count_stmt)
            return f"{cls.name} ({count})"
        return cls.name


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

    def __post_init__(self):
        """
        Регистрирует админку для приложения
        """
        apps_admins.append(self)
        logger.info(f'Registered "{self.verbose_name}" admin')

    def register(self, admin_model: type[ModelAdmin]):
        self.admin_models.append(admin_model)


apps_admins: list[AppAdmin] = []
