import datetime

from sqlalchemy import MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
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

    id: Mapped[int] = mapped_column(
        sqltypes.Integer,
        nullable=False,
        primary_key=True,
        autoincrement=True,
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
