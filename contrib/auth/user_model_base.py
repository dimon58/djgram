"""
Модели для базы данных
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, func
from sqlalchemy.orm import Mapped, relationship, declared_attr
from sqlalchemy.sql import sqltypes

from djgram.contrib.telegram.models import TelegramUser
from djgram.db.models import TimeTrackableBaseModel


# pylint: disable=too-few-public-methods
class AbstractUser(TimeTrackableBaseModel):
    """
    Модель пользователя
    """

    __abstract__ = True

    is_admin: Mapped[bool] = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Является ли пользователь администратором",
    )
    telegram_user_id: Mapped[int] = Column(
        ForeignKey(TelegramUser.id, ondelete="SET NULL"),
        nullable=True,
        doc="id пользователя в telegram. Он же id чата с ним.",
    )

    @declared_attr
    def telegram_user(self) -> Mapped[TelegramUser]:
        return relationship(TelegramUser)

    first_seen: Mapped[datetime] = Column(
        sqltypes.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )
    last_interaction = Column(
        sqltypes.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )
