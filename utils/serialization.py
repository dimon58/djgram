from typing import Any, TypeAlias

import pydantic

Json: TypeAlias = dict | list | float | int | str | bool | None


def jsonify(data: Any) -> Json:
    """
    Превращает любой тип в сериализируемый в json, например с помощью orjson
    """
    if isinstance(data, list):
        return [jsonify(elem) for elem in data]

    if isinstance(data, pydantic.BaseModel):
        return data.model_dump(mode="python", exclude_unset=True)

    return data
