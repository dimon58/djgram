# ruff: noqa
# type: ignore
import pydantic
import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemyv2_nested_mutable import MutablePydanticBaseModel, TrackedList, TrackedPydanticBaseModel


class Base(DeclarativeBase):
    pass


class Addresses(MutablePydanticBaseModel):
    class AddressItem(pydantic.BaseModel):
        street: str
        city: str
        area: str | None = None

    preferred: AddressItem | None = None
    work: list[AddressItem] = []
    home: list[AddressItem] = []
    updated_time: str | None = None

    def __init__(self, **data):
        super().__init__(**data)


@pytest.fixture(scope="module", autouse=True)
def mapper():
    return Base


@pytest.fixture
def user1():
    return User(name="foo", addresses={"preferred": {"street": "bar", "city": "baz", "area": None}})


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(30))
    addresses: Mapped[Addresses | None] = mapped_column(Addresses.as_mutable(JSON()), nullable=True)


def test_mutable_pydantic_type(session: Session, user1: User):

    # Arrange
    u = user1

    # Act
    session.add(u)
    session.commit()

    # Assert
    assert isinstance(u.addresses, MutablePydanticBaseModel)
    assert isinstance(u.addresses.preferred, Addresses.AddressItem)
    assert isinstance(u.addresses.preferred, TrackedPydanticBaseModel)
    assert isinstance(u.addresses.home, TrackedList)
    assert type(u.addresses.preferred).__name__ == "TrackedAddressItem"


def test_mutable_pydantic_type_shallow_change(session: Session, user1: User):

    # Arrange
    u = user1
    session.add(u)
    session.commit()

    # Act - Shallow change
    a = u.addresses
    assert a is not None

    a.updated_time = "2021-01-01T00:00:00"
    session.commit()

    # Assert
    assert a.updated_time == "2021-01-01T00:00:00"


def test_mutable_pydantic_type_deep_change(session: Session, user1: User):

    # Arrange
    u = user1
    session.add(u)
    session.commit()

    # Act - Deep change (assert to avoid type check errors)
    a = u.addresses
    assert a is not None
    p = a.preferred
    assert p is not None
    p.street = "bar2"
    session.commit()

    # Assert
    assert a is not None
    assert p is not None
    assert p.model_dump(exclude_none=True) == {"street": "bar2", "city": "baz"}


def test_mutable_pydantic_type_deep_append(session: Session, user1: User):

    # Arrange
    u = user1
    session.add(u)
    session.commit()

    # Act - Append item
    assert u.addresses is not None
    u.addresses.home.append(Addresses.AddressItem.model_validate({"street": "bar1", "city": "baz"}))
    session.commit()

    # Assert
    assert u.addresses.home[0].model_dump(exclude_none=True) == {"street": "bar1", "city": "baz"}
    assert isinstance(u.addresses.home[0], TrackedPydanticBaseModel)
    assert isinstance(u.addresses.home[0], Addresses.AddressItem)


def test_mutable_pydantic_type_deep_pop(session: Session, user1: User):

    # Arrange
    u = user1
    assert u.addresses is not None
    u.addresses.home.append(Addresses.AddressItem.model_validate({"street": "bar1", "city": "baz"}))
    u.addresses.home.append(Addresses.AddressItem.model_validate({"street": "bar2", "city": "baz"}))
    u.addresses.home.append(Addresses.AddressItem.model_validate({"street": "bar3", "city": "baz"}))
    session.add(u)
    session.commit()

    # Act - Pop last item from list
    u.addresses.home.pop(2)
    session.commit()

    # Assert
    assert u.addresses.preferred is not None
    assert u.addresses.preferred.model_dump(exclude_none=True) == {"street": "bar", "city": "baz"}
    assert u.addresses.home[0].model_dump(exclude_none=True) == {"street": "bar1", "city": "baz"}
    assert u.addresses.home[1].model_dump(exclude_none=True) == {"street": "bar2", "city": "baz"}
    assert len(u.addresses.home) == 2
