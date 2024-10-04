from collections.abc import Hashable, Sequence
from typing import Any


def set_value_using_composite_key(data: dict, key: Sequence[Hashable], value: Any) -> None:
    """
    Устанавливает значение в словаре по сложному ключу

    data = {}
    print(data)  # {}
    set_value_using_composite_key(data, ["key1", 2, "key3"], "test_data")
    print(data)  # {'key1': {2: {'key3': 'test_data'}}}
    """
    if len(key) == 0:
        raise ValueError("Empty key")
    for key_part in key[:-1]:
        data = data.setdefault(key_part, {})
    data[key[-1]] = value
