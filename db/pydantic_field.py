from typing import TypeVar

import pydantic
from sqlalchemy import JSON
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy_nested_mutable.mutable import MutablePydanticBaseModel, PydanticType

_P = TypeVar("_P", bound=pydantic.BaseModel)


def PydanticField(pydantic_type: type[_P], json_sql_type: TypeEngine | None = None) -> PydanticType[_P]:  # noqa: N802
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

    # Гарантируем, что содержательный класс является первым родителем
    # Чтобы получить к нему доступ:
    #   generated = PydanticField(Type)
    #   OriginalType = generated.pydantic_type.__bases__[0]
    #   generated is Type == True
    # noinspection PyUnresolvedReferences
    return type(pydantic_type.__class__.__name__, (pydantic_type, MutablePydanticBaseModel), {}).as_mutable(
        json_sql_type
    )
