import datetime

from sqlalchemy import MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from sqlalchemy.sql import sqltypes
from uuid6 import UUID, uuid7

from djgram.configs import DB_METADATA
from djgram.utils.misc import utcnow


class Base(DeclarativeBase):  # noqa: D101
    metadata = DB_METADATA or MetaData()


class BaseModel(Base):
    """
    Абстрактная базовая модель с id
    """

    __abstract__ = True
    metadata = DB_METADATA or MetaData()

    id: Mapped[int] = mapped_column(
        sqltypes.BigInteger,
        nullable=False,
        primary_key=True,
        autoincrement=True,
        doc="The primary identifier of the object",
    )

    def __repr__(self):
        """
        Отображается в админке
        """
        return f"{self.__class__.__name__}<{self.id!r}>"

    # noinspection PyMethodParameters,SpellCheckingInspection
    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        return cls.__name__.lower()


class UUIDBaseModel(BaseModel):
    """
    Модель с первичным ключом UUIDv7
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(  # pyright: ignore [reportIncompatibleVariableOverride]
        sqltypes.UUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid7,  # Генерация UUIDv7 по умолчанию
        doc="The primary identifier of the object",
    )


class CreatedAtMixin:
    """
    Примесь для моделей со временем создания
    """

    created_at: Mapped[datetime.datetime] = mapped_column(
        sqltypes.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Date of creation of the object",
    )


class UpdatedAtMixin:
    """
    Примесь для моделей со временем обновления
    """

    updated_at: Mapped[datetime.datetime] = mapped_column(
        sqltypes.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=utcnow,
        doc="The date of the last update of the object",
    )


class TimeTrackableMixin(CreatedAtMixin, UpdatedAtMixin):
    """
    Примесь для моделей со временем создания и обновления
    """


class TimeTrackableBaseModel(TimeTrackableMixin, BaseModel):
    """
    Абстрактная базовая модель со временем создания и обновления
    """

    __abstract__ = True
