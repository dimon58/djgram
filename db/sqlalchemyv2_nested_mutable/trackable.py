from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Self, cast, overload
from weakref import WeakValueDictionary

import pydantic
from sqlalchemy.ext.mutable import Mutable

from ._typing import KT, VT, T

if TYPE_CHECKING:
    from sqlalchemy.util.typing import SupportsIndex, TypeGuard

parents_track: WeakValueDictionary[int, TrackedObject] = WeakValueDictionary()


class TrackedObject:
    """
    Represents an object in a nested context whose parent can be tracked.

    The top object in the parent link should be an instance of `Mutable`.
    """

    def __del__(self):
        if (id_ := id(self)) in parents_track:
            del parents_track[id_]

    def changed(self) -> None:
        if (id_ := id(self)) in parents_track:
            parent = parents_track[id_]
            parent.changed()
        elif isinstance(self, Mutable):
            s = cast(Mutable, super())
            s.changed()

    @classmethod
    @overload
    def make_nested_trackable(
        cls,
        value: dict[KT, VT],
        parent: TrackedObject,
    ) -> TrackedDict[KT, VT | TrackedObject]: ...

    @classmethod
    @overload
    def make_nested_trackable(cls, value: list[T], parent: TrackedObject) -> TrackedList[T | TrackedObject]: ...

    @classmethod
    @overload
    def make_nested_trackable(cls, value: pydantic.BaseModel, parent: TrackedObject) -> TrackedPydanticBaseModel: ...

    @classmethod
    @overload
    def make_nested_trackable(cls, value: T, parent: TrackedObject) -> T: ...

    @classmethod
    def make_nested_trackable(cls, value: T, parent: TrackedObject) -> TrackedObject | T:
        # val: dict[KT, VT] | list[T] | pydantic.BaseModel | TrackedPydanticBaseModel | TrackedObject | T noqa: ERA001
        # -> TrackedDict[KT, VT | TrackedObject] | TrackedList[T]
        # | TrackedObject] | TrackedPydanticBaseModel | TrackedObject | T:
        new_val = value

        if isinstance(value, dict):
            new_val = TrackedDict((k, cls.make_nested_trackable(v, parent)) for k, v in value.items())
        elif isinstance(value, list):
            new_val = TrackedList(cls.make_nested_trackable(o, parent) for o in value)
        elif isinstance(value, pydantic.BaseModel) and not isinstance(value, TrackedPydanticBaseModel):
            # noinspection PyTypeChecker
            model_cls: type[TrackedPydanticBaseModel] = type(
                "Tracked" + value.__class__.__name__,
                (TrackedPydanticBaseModel, value.__class__),
                {},
            )
            model_cls.__doc__ = (
                f"This class is composed of `{value.__class__.__name__}` and `TrackedPydanticBaseModel` "
                "to make it trackable in nested context."
            )
            new_val = model_cls.model_validate(value.model_dump())

        if isinstance(new_val, cls):
            parents_track[id(new_val)] = parent

        return new_val


class TrackedList(TrackedObject, list[T]):  # noqa: D101
    def __reduce_ex__(self, proto: SupportsIndex) -> tuple[type[TrackedList[T]], tuple[list[T]]]:
        return self.__class__, (list(self),)

    # needed for backwards compatibility with
    # older pickles
    def __setstate__(self, state: Iterable[T]) -> None:
        self[:] = state

    def is_scalar(self, value: T | Iterable[T]) -> TypeGuard[T]:
        return not isinstance(value, Iterable)

    def is_iterable(self, value: T | Iterable[T]) -> TypeGuard[Iterable[T]]:
        return isinstance(value, Iterable)

    if not TYPE_CHECKING:

        def __setitem__(self, index: SupportsIndex | slice, value: T | Iterable[T]) -> None:
            """Detect list set events and emit change events."""

            super().__setitem__(index, TrackedObject.make_nested_trackable(value, self))
            self.changed()

    def __delitem__(self, index: SupportsIndex | slice) -> None:
        """Detect list del events and emit change events."""
        super().__delitem__(index)
        self.changed()

    def pop(self, *arg: SupportsIndex) -> T:
        result = super().pop(*arg)
        self.changed()
        return result

    def append(self, __object: T) -> None:
        super().append(TrackedObject.make_nested_trackable(__object, self))  # pyright: ignore [reportArgumentType]
        self.changed()

    def extend(self, __iterable: Iterable[T]) -> None:
        super().extend(
            TrackedObject.make_nested_trackable(value, self)  # pyright: ignore [reportArgumentType]
            for value in __iterable
        )
        self.changed()

    def __iadd__(self, value: Iterable[T]) -> Self:
        self.extend(value)
        return self

    def insert(self, __index: SupportsIndex, __object: T) -> None:
        super().insert(
            __index,
            TrackedObject.make_nested_trackable(__object, self),  # pyright: ignore [reportArgumentType]
        )
        self.changed()

    def remove(self, i: T) -> None:
        super().remove(i)
        self.changed()

    def clear(self) -> None:
        super().clear()
        self.changed()

    def sort(self, **kw: Any) -> None:
        super().sort(**kw)
        self.changed()

    def reverse(self) -> None:
        super().reverse()
        self.changed()


class TrackedDict(TrackedObject, dict[KT, VT]):  # noqa: D101
    def __setitem__(self, key: KT, value: VT) -> None:
        """Detect dictionary set events and emit change events."""
        super().__setitem__(key, value)
        self.changed()

    if TYPE_CHECKING:
        # from https://github.com/python/mypy/issues/14858

        @overload
        def setdefault(self: TrackedDict[KT, T | None], key: KT, value: None = None) -> T | None: ...

        @overload
        def setdefault(self, key: KT, value: VT) -> VT: ...

        def setdefault(  # pyright: ignore [reportIncompatibleMethodOverride]
            self,
            key: KT,
            value: object = None,
        ) -> object: ...

    else:

        def setdefault(self, key, value=None):  # noqa: ANN001, ANN201
            result = super().setdefault(key, TrackedObject.make_nested_trackable(value, self))
            self.changed()
            return result

    def __delitem__(self, key: KT) -> None:
        """Detect dictionary del events and emit change events."""
        super().__delitem__(key)
        self.changed()

    def update(self, *a: Any, **kw: VT) -> None:
        a = tuple(TrackedObject.make_nested_trackable(e, self) for e in a)
        kw = {k: TrackedObject.make_nested_trackable(v, self) for k, v in kw.items()}
        super().update(*a, **kw)
        self.changed()

    if TYPE_CHECKING:

        @overload
        def pop(self, __key: KT) -> VT: ...

        @overload
        def pop(self, __key: KT, __default: VT | T) -> VT | T: ...

        def pop(self, __key: KT, __default: VT | T | None = None) -> VT | T: ...

    else:

        def pop(self, *arg):  # noqa: ANN201
            result = super().pop(*arg)
            self.changed()
            return result

    def popitem(self) -> tuple[KT, VT]:
        result = super().popitem()
        self.changed()
        return result

    def clear(self) -> None:
        super().clear()
        self.changed()

    def __setstate__(self, state: dict[str, int] | dict[str, str]) -> None:
        self.update(state)


class TrackedPydanticBaseModel(TrackedObject, Mutable, pydantic.BaseModel):  # noqa: D101
    @classmethod
    def coerce(cls, key: str, value: Any) -> TrackedPydanticBaseModel:
        return value if isinstance(value, cls) else cls.model_validate(value)

    def __init__(self, **data):  # noqa: D107
        super().__init__(**data)
        for field in self.model_fields:
            setattr(self, field, TrackedObject.make_nested_trackable(getattr(self, field), self))

    def __setattr__(self, name: str, value: Any):
        prev_value = getattr(self, name, None)
        super().__setattr__(name, value)
        if prev_value != getattr(self, name):
            self.changed()
