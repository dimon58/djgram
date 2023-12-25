"""
Базовые классы для работы приложения администрирования
"""
import logging
import sys
from dataclasses import dataclass
from dataclasses import field as dc_field

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import sqltypes

from djgram.configs import ADMIN_ROWS_PER_PAGE
from djgram.db.models import Base
from djgram.db.utils import get_fields_of_model

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class ModelAdmin:
    """
    Модель админки, как в django (не относится к базе данных на прямую)
    """

    model: type[Base] = None  # Модель
    name: str = ""  # Название
    list_display: list[str] = []  # Список колонок для показа при предпросмотре
    search_fields: list[str] = []  # Список полей, по которым производиться поиск
    show_count: bool = True  # Показывать число записей
    show_docs: bool = True  # Показывать документацию, если есть

    skip_synonyms_origin: bool = True  # Не показывать поля, для которых есть синонимы

    @classmethod
    def __check_fields_exists(cls, fields, allowed_fields, list_name):
        extra_fields = set(fields) - allowed_fields

        errors = set()
        for extra_field in extra_fields:
            if "__" not in extra_field:  # todo добавить валидацию таких полей - полей у внешних ключей
                errors.add(extra_field)

        if len(errors) > 0:
            logger.critical(f"У {cls} есть лишние поля в {list_name}: {sorted(errors)}")
            sys.exit()

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

        allowed_fields = set(get_fields_of_model(cls.model, skip_synonyms_origin=False))
        cls.__check_fields_exists(cls.list_display, allowed_fields, "list_display")
        cls.__check_fields_exists(cls.search_fields, allowed_fields, "search_fields")

    @classmethod
    async def display_name(cls, db_session: AsyncSession) -> str:
        if cls.show_count:
            count_stmt = select(func.count("*")).select_from(cls.model)
            count = await db_session.scalar(count_stmt)
            return f"{cls.name} ({count})"
        return cls.name

    @classmethod
    def get_fields_of_model(cls) -> list[str]:
        return get_fields_of_model(cls.model, cls.skip_synonyms_origin)

    @classmethod
    def generate_search_filter(cls, query: str):
        ors = []

        allowed_fields = set(get_fields_of_model(cls.model, skip_synonyms_origin=True))
        ilike_query = None
        for field_name in set(cls.search_fields) & allowed_fields:  # todo: добавить фильтрацию по внешним ключам
            field = getattr(cls.model, field_name)
            # Все возможные Varchar, Char, Text - подклассы String
            if isinstance(field.type, sqltypes.String):
                if ilike_query is None:
                    ilike_query = f"%{query}%"
                ors.append(field.ilike(ilike_query))
            else:
                ors.append(field == query)

        return or_(*ors)


@dataclass
class AppAdmin:
    """
    Модель администрирования для приложения

    Attributes:
        verbose_name(str): Человекочитаемое название приложение
        admin_models(list[ModelAdmin]): Список всех административных панелей в приложении
    """

    verbose_name: str

    admin_models: list[type[ModelAdmin]] = dc_field(default_factory=list)

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
