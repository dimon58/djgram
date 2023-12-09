import datetime

from sqlalchemy import Column, func
from sqlalchemy.orm import Mapped, declarative_base, declared_attr
from sqlalchemy.sql import sqltypes

from djgram.configs import DB_METADATA
from djgram.utils import utcnow

Base = declarative_base(metadata=DB_METADATA)


class BaseEmptyModel(Base):
    """
    Абстрактная базовая модель
    """

    __abstract__ = True

    # pylint: disable=no-self-argument
    # noinspection PyMethodParameters,SpellCheckingInspection
    @declared_attr
    def __tablename__(cls) -> str:  # noqa: N805
        return cls.__name__.lower()


class BaseModel(BaseEmptyModel):
    """
    Абстрактная базовая модель с id
    """

    __abstract__ = True

    id: Mapped[int] = Column(
        sqltypes.Integer,
        nullable=False,
        primary_key=True,
        autoincrement=True,
    )

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id!r})>"


class CreatedAtMixin:
    """
    Примесь для моделей со временем создания
    """

    created_at: Mapped[datetime.datetime] = Column(
        sqltypes.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )


class UpdatedAtMixin:
    """
    Примесь для моделей со временем обновления
    """

    updated_at: Mapped[datetime.datetime] = Column(
        sqltypes.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
        server_onupdate=func.now(),
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
