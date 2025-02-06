"""
Модели для базы данных
"""

from datetime import datetime

from djgram.contrib.telegram.models import TelegramUser
from djgram.db.models import BaseModel, UpdatedAtMixin
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.sql import sqltypes


# pylint: disable=too-few-public-methods
class AbstractUser(UpdatedAtMixin, BaseModel):
    """
    Модель пользователя
    """

    __abstract__ = True

    banned: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        default=False,
        nullable=False,
        doc="Забанен ли пользователь",
    )

    is_admin: Mapped[bool] = mapped_column(
        sqltypes.Boolean,
        default=False,
        nullable=False,
        doc="Является ли пользователь администратором",
    )
    telegram_user_id: Mapped[int] = mapped_column(
        ForeignKey(TelegramUser.id, ondelete="SET NULL"),
        nullable=False,
        doc="id пользователя в telegram. Он же id чата с ним.",
    )
    telegram_user: Mapped[TelegramUser] = relationship(  # pyright: ignore [reportRedeclaration, reportAssignmentType]
        TelegramUser,
    )

    @declared_attr
    def telegram_user(self) -> Mapped[TelegramUser]:  # noqa: F811
        return relationship(TelegramUser, lazy="selectin")

    first_seen: Mapped[datetime] = mapped_column(
        sqltypes.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )
    last_interaction: Mapped[datetime] = mapped_column(
        sqltypes.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # pylint: disable=not-callable
    )
