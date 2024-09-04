import datetime

from sqlalchemy import MetaData, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, DeclarativeBase
from sqlalchemy.sql import sqltypes

from djgram.configs import DB_METADATA
from djgram.utils import utcnow


class Base(DeclarativeBase):
    metadata = DB_METADATA or MetaData()


class BaseModel(Base):
    """
    Абстрактная базовая модель с id
    """

    __abstract__ = True
    metadata = DB_METADATA or MetaData()

    id: Mapped[int] = mapped_column(
        sqltypes.Integer,
        nullable=False,
        primary_key=True,
        autoincrement=True,
        doc="The primary identifier of the object",
    )

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id!r})>"

    # pylint: disable=no-self-argument
    # noinspection PyMethodParameters,SpellCheckingInspection
    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        return cls.__name__.lower()


class CreatedAtMixin:
    """
    Примесь для моделей со временем создания
    """

    created_at: Mapped[datetime.datetime] = mapped_column(
        sqltypes.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
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
