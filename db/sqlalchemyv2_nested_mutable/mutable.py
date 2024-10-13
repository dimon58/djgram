from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar, cast

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy import Dialect
from sqlalchemy.ext.mutable import Mutable

from ._typing import KT, VT, T
from .trackable import TrackedDict, TrackedList, TrackedObject, TrackedPydanticBaseModel

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlalchemy.sql.type_api import TypeEngine

_P = TypeVar("_P", bound="MutablePydanticBaseModel")
DB_JSON = TypeVar("DB_JSON", bound=sa.JSON)

default_json = sa.JSON()


class MutableList(TrackedList[T], Mutable):
    """
    A mutable list that tracks changes to itself and its children.

    Used as top-level mapped object. e.g.

        aliases: Mapped[list[str]] = mapped_column(MutableList.as_mutable(ARRAY(String(128))))
        schedule: Mapped[list[list[str]]] = mapped_column(MutableList.as_mutable(ARRAY(sa.String(128), dimensions=2)))
    """

    @classmethod
    def coerce(cls, key: str, value: Any) -> MutableList[T]:
        return value if isinstance(value, cls) else cls(value)

    def __init__(self, __iterable: Iterable[T] | None = None):  # noqa: D107
        if __iterable is None:
            __iterable = []

        super().__init__(TrackedObject.make_nested_trackable(cast(Iterable[T], __iterable), self))


class MutableDict(TrackedDict[KT, VT], Mutable):
    @classmethod
    def coerce(cls, key: str, value: Any) -> MutableDict[KT, VT]:
        return value if isinstance(value, cls) else cls(value)

    def __init__(self, source: Mapping[KT, VT] | Iterable[tuple[KT, VT]] = (), **kwds):  # noqa: D107
        super().__init__(  # pyright: ignore [reportCallIssue]
            TrackedObject.make_nested_trackable(dict(source, **kwds), self)  # pyright: ignore [reportArgumentType]
        )


class PydanticType(sa.types.TypeDecorator[_P], Generic[_P, DB_JSON]):
    """
    Inspired by https://gist.github.com/imankulov/4051b7805ad737ace7d8de3d3f934d6b
    """

    cache_ok = True
    impl = sa.types.JSON

    def __init__(  # noqa: D107
        self,
        pydantic_type: type[_P],
        sqltype: TypeEngine[DB_JSON] = default_json,
        use_jsonb_if_postgres: bool = True,
    ):
        super().__init__()
        if not issubclass(pydantic_type, BaseModel):
            raise TypeError(f"pydantic_type should be subclass of BaseModel not {type(pydantic_type)}")

        self.pydantic_type = pydantic_type
        self.sqltype = sqltype
        self.use_jsonb_if_postgres = use_jsonb_if_postgres

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[DB_JSON]:

        if dialect.name == "postgresql" and self.use_jsonb_if_postgres:
            from sqlalchemy.dialects.postgresql import JSONB

            return dialect.type_descriptor(JSONB())

        return dialect.type_descriptor(self.sqltype)

    def __repr__(self):
        # NOTE: the `__repr__` is used by Alembic to generate the migration script.
        return f"{self.__class__.__name__}({self.pydantic_type.__name__})"

    def process_bind_param(self, value: _P | None, dialect: Dialect):
        return value.model_dump(mode="json") if value else None

    def process_result_value(self, value: Any, dialect: Dialect) -> _P | None:
        return self.pydantic_type.model_validate(value) if value else None


class MutablePydanticBaseModel(TrackedPydanticBaseModel, Mutable, Generic[DB_JSON]):
    @classmethod
    def coerce(cls, key: str, value: Any) -> MutablePydanticBaseModel:
        return value if isinstance(value, cls) else cls.model_validate(value)

    def dict(self, *args, **kwargs):
        res = super().model_dump(*args, **kwargs)
        res.pop("_parents", None)
        return res

    @classmethod
    def as_mutable(  # pyright: ignore [reportIncompatibleMethodOverride]
        cls,
        sqltype: TypeEngine[DB_JSON] = default_json,
    ) -> TypeEngine[Self]:
        return super().as_mutable(PydanticType(cls, sqltype))
