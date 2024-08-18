from typing import Any, Self, TypeVar

import pydantic
from alembic.autogenerate.api import AutogenContext
from sqlalchemy import JSON
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemyv2_nested_mutable import TrackedPydanticBaseModel
from sqlalchemyv2_nested_mutable.mutable import PydanticType

_T = TypeVar("_T", bound=Any)
_P = TypeVar("_P", bound=pydantic.BaseModel)


class ExtendedPydanticType(PydanticType[_P]):  # pyright: ignore [reportInvalidTypeArguments]
    cache_ok = True

    @classmethod
    def get_alembic_import_name(cls) -> str:
        return "PydanticField"

    def get_base_type_for_alembic(self):
        return self.pydantic_type.__bases__[0]

    def alembic_definition(self, autogen_context: AutogenContext):

        alembic_import_name = self.get_alembic_import_name()

        autogen_context.imports.add(f"from {self.__module__} import {alembic_import_name}")

        # .pydantic_type.__bases__[0] guaranteed by PydanticField function
        base_type: type = self.get_base_type_for_alembic()
        autogen_context.imports.add(f"import {base_type.__module__}")

        if self.sqltype is None:
            json_sql_type = ""
        else:
            autogen_context.imports.add(f"import {self.sqltype.__module__}")
            sql_type_name = self.sqltype.__name__ if isinstance(self.sqltype, type) else self.sqltype.__class__.__name__

            json_sql_type = f", {self.sqltype.__module__}.{sql_type_name}()"

        return f"{alembic_import_name}({base_type.__module__}.{base_type.__name__}{json_sql_type})"


class ImmutablePydanticField(ExtendedPydanticType[_P]):
    cache_ok = True

    def __init__(self, pydantic_type: type[_P], sqltype: TypeEngine[_T] | None = None):  # noqa: D107
        if not pydantic_type.model_config.get("frozen"):
            raise TypeError(f"pydantic_type {pydantic_type} should be frozen. Use PydanticField instead.")

        super().__init__(pydantic_type, sqltype)

    @classmethod
    def get_alembic_import_name(cls) -> str:
        return cls.__name__

    def get_base_type_for_alembic(self):
        return self.pydantic_type


class ExtendedMutablePydanticBaseModel(TrackedPydanticBaseModel, Mutable):

    @classmethod
    def coerce(cls, key: str, value: Any) -> Self:  # noqa: ARG003
        if isinstance(value, cls):
            return value

        if isinstance(value, pydantic.BaseModel):
            value = value.model_dump()

        return cls.model_validate(value)

    def dict(self, *args, **kwargs):
        res = super().model_dump(*args, **kwargs)
        res.pop("_parents", None)
        return res

    @classmethod
    def as_mutable(cls, sqltype: TypeEngine[_T] | None = None) -> TypeEngine[ExtendedPydanticType[Self]]:
        return super().as_mutable(ExtendedPydanticType(cls, sqltype))


def PydanticField(  # noqa: N802
    pydantic_type: type[_P], json_sql_type: TypeEngine | None = None
) -> TypeEngine[ExtendedPydanticType[_P]]:
    """
    Возвращает обёртку над json в виде pydantic_type, которая позволяет отслеживать вложенные изменения в данных

    https://github.com/wonderbeyond/SQLAlchemy-Nested-Mutable

    :param pydantic_type: базовый тип pydantic
    :param json_sql_type: тип хранения в базе данных (JSON и JSONB)
    """

    if json_sql_type is not None and (
        isinstance(json_sql_type, type)
        and not issubclass(json_sql_type, JSON)
        or not isinstance(json_sql_type, type)
        and not isinstance(json_sql_type, JSON)
    ):
        raise TypeError(f"json_sql_type should be subclass or instance of JSON, but got {json_sql_type}")

    if pydantic_type.model_config.get("frozen"):
        raise TypeError(f"pydantic_type {pydantic_type} should not be frozen. Use ImmutablePydanticField instead.")

    # Гарантируем, что содержательный класс является первым родителем
    # Чтобы получить к нему доступ:
    #   generated = PydanticField(Type)
    #   OriginalType = generated.pydantic_type.__bases__[0]
    #   generated is Type == True
    # noinspection PyUnresolvedReferences
    return type(  # pyright: ignore [reportGeneralTypeIssues, reportReturnType]
        pydantic_type.__class__.__name__, (pydantic_type, ExtendedMutablePydanticBaseModel), {}
    ).as_mutable(json_sql_type)
