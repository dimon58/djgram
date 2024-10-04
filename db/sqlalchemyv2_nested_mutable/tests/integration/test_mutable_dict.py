import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemyv2_nested_mutable import MutableDict, TrackedDict, TrackedList


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(30))
    addresses: Mapped[MutableDict] = mapped_column(MutableDict.as_mutable(JSONB()), default=MutableDict)


@pytest.fixture
def user1():
    return User(
        name="foo",
        addresses={
            "home": {"street": "123 Main Street", "city": "New York"},
            "work": "456 Wall Street",
        },
    )


@pytest.fixture
def user2():
    return User(
        name="bar",
        addresses={
            "home": {"street": "123 Main Street", "city": "New York"},
            "work": "456 Wall Street",
            "others": [
                {"label": "secret0", "address": "789 Moon Street"},
            ],
        },
    )


@pytest.fixture(scope="module", autouse=True)
def mapper():
    return Base


def test_mutable_dict(session: Session, user1: User):

    # Arrange
    u = user1

    # Act
    session.add(u)
    session.commit()

    # Assert
    assert isinstance(u.addresses, MutableDict)
    assert u.addresses["home"] == {"street": "123 Main Street", "city": "New York"}
    assert isinstance(u.addresses["home"], TrackedDict)
    assert isinstance(u.addresses["work"], str)


def test_mutable_dict_shallow_change(session: Session, user1: User):

    # Arrange
    u = user1
    session.add(u)
    session.commit()

    # Act - Shallow change
    u.addresses["realtime"] = "999 RT Street"
    session.commit()

    # Assert
    assert u.addresses["realtime"] == "999 RT Street"


def test_mutable_dict_deep_change(session: Session, user1: User):

    # Arrange
    u = user1
    session.add(u)
    session.commit()

    # Act - Deep change
    u.addresses["home"]["street"] = "124 Main Street"
    session.commit()

    # Assert
    assert u.addresses["home"] == {"street": "124 Main Street", "city": "New York"}


def test_mutable_dict_update(session: Session, user1: User):

    # Arrange
    u = user1
    session.add(u)
    session.commit()

    # Act - Change by update()
    u.addresses["home"].update({"street": "125 Main Street"})
    session.commit()

    # Assert
    assert u.addresses["home"] == {"street": "125 Main Street", "city": "New York"}


def test_mutable_dict_update2(session: Session, user1: User):

    # Arrange
    u = user1
    session.add(u)
    session.commit()

    # Act
    u.addresses["home"].update({"area": "America"}, street="126 Main Street")
    session.commit()

    # Assert
    assert u.addresses["home"] == {"street": "126 Main Street", "city": "New York", "area": "America"}


def test_mutable_dict_mixed_with_list(session: Session, user2: User):

    # Arrange
    u = user2

    # Act
    session.add(u)
    session.commit()

    # Assert
    assert isinstance(u.addresses["others"], TrackedList)
    assert u.addresses["others"] == [{"label": "secret0", "address": "789 Moon Street"}]


def test_mutable_dict_mixed_with_list_deep_change(session: Session, user2: User):

    # Arrange
    u = user2

    # Act - Deep change on list value
    u.addresses["others"].append({"label": "secret1", "address": "790 Moon Street"})
    session.commit()

    # Assert
    assert u.addresses["others"] == [
        {"label": "secret0", "address": "789 Moon Street"},
        {"label": "secret1", "address": "790 Moon Street"},
    ]


def test_mutable_dict_mixed_with_list_deep_changes(session: Session, user2: User):

    # Arrange
    u = user2

    # Act - Deep change across list and dict values
    u.addresses["others"].append({"label": "secret1", "address": "790 Moon Street"})
    u.addresses["others"][1].update(address="791 Moon Street")
    session.commit()

    # Assert
    assert u.addresses["others"] == [
        {"label": "secret0", "address": "789 Moon Street"},
        {"label": "secret1", "address": "791 Moon Street"},
    ]
