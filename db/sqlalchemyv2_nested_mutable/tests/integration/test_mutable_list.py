# ruff: noqa
# type: ignore
import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemyv2_nested_mutable import MutableList, TrackedDict, TrackedList


class Base(DeclarativeBase):
    pass


class User(Base):
    """Use STRING to store array data and assign default"""

    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(30))
    aliases: Mapped[MutableList[str]] = mapped_column(
        MutableList[str].as_mutable(ARRAY(sa.String(128))), default=MutableList[str]
    )

    schedule: Mapped[MutableList[list[str]]] = mapped_column(
        MutableList[list[str]].as_mutable(ARRAY(sa.String(128), dimensions=2)), default=MutableList[str]
    )
    # a user's weekly schedule, e.g. [ ['meeting', 'launch'], ['training', 'presentation'] ]


class UserV2(Base):
    """Use JSONB to store array data"""

    __tablename__ = "user_account_v2"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(30))
    aliases: Mapped[MutableList[str]] = mapped_column(MutableList[str].as_mutable(JSONB()), default=MutableList[str])
    schedule: Mapped[MutableList[list[str]]] = mapped_column(
        MutableList[list[str]].as_mutable(JSONB()), default=MutableList[list[str]]
    )


class UserV3(Base):
    """Use JSONB to store array data BUT no defaults for aliases and schedule SO should be NONE"""

    __tablename__ = "user_account_v3"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(30))
    aliases: Mapped[MutableList[str] | None] = mapped_column(MutableList[str].as_mutable(JSONB()), nullable=True)
    schedule: Mapped[MutableList[list[str]] | None] = mapped_column(
        MutableList[list[str]].as_mutable(JSONB()), nullable=True
    )


@pytest.fixture(scope="module", autouse=True)
def mapper():
    return Base


@pytest.fixture
def user1_1():
    return User(name="foo", aliases=["bar", "baz"])


@pytest.fixture
def user1_2():
    return User(name="foo", schedule=[["meeting", "launch"], ["training", "presentation"]])


@pytest.fixture
def user1_3():
    return User(name="foo", schedule=[["meeting", "launch"], ["training", "presentation"], ["breakfast", "consulting"]])


@pytest.fixture
def user2_1():
    return UserV2(name="foo", aliases=["bar", "baz"])


@pytest.fixture
def user2_2():
    return UserV2(name="foo", schedule=[["meeting", "launch"], ["training", "presentation"]])


def test_mutable_list_aliases(session: Session, user1_1: User):

    # Arrange
    u = user1_1

    # Act
    session.add(u)
    session.commit()

    # Assert
    assert isinstance(u.aliases, MutableList)
    assert u.aliases == ["bar", "baz"]
    assert u.name == "foo"


def test_mutable_list_aliases_append(session: Session, user1_1: User):

    # Arrange
    u = user1_1
    session.add(u)
    session.commit()

    # Act
    u.aliases.append("qux")
    session.commit()

    # Assert
    assert u.aliases == ["bar", "baz", "qux"]
    assert isinstance(u.aliases, MutableList)
    assert u.name == "foo"


def test_nested_mutable_list_schedule(session: Session, user1_2: User):

    # Arrange
    u = user1_2

    # Act
    session.add(u)
    session.commit()

    # Assert
    assert u.schedule == [["meeting", "launch"], ["training", "presentation"]]


def test_nested_mutable_list_schedule_mutate_top_level(session: Session, user1_2: User):

    # Arrange
    u = user1_2
    session.add(u)
    session.commit()

    # Act - Mutation at top level
    u.schedule.append(["breakfast", "consulting"])
    session.commit()

    assert u.schedule == [["meeting", "launch"], ["training", "presentation"], ["breakfast", "consulting"]]


def test_nested_mutable_list_schedule_mutate_nested(session: Session, user1_3: User):

    # Arrange
    u = user1_3
    session.add(u)
    session.commit()

    # Act - Mutation at nested level
    u.schedule[0][0] = "breakfast"
    session.commit()

    # Assert
    assert u.schedule == [["breakfast", "launch"], ["training", "presentation"], ["breakfast", "consulting"]]


def test_nested_mutable_list_schedule_mutate_pop(session: Session, user1_3: User):

    # Arrange
    u = user1_3
    session.add(u)
    session.commit()

    # Act - Mutation at nested level
    u.schedule.pop()
    session.commit()

    # Assert
    assert u.schedule == [["meeting", "launch"], ["training", "presentation"]]


def test_mutable_list_stored_as_jsonb(session: Session, user2_1: User):

    # Arrange
    u = user2_1

    # Act
    session.add(u)
    session.commit()

    # Assert
    assert isinstance(u.aliases, MutableList)
    assert u.aliases == ["bar", "baz"]


def test_mutable_list_stored_as_jsonb_append(session: Session, user2_1: User):

    # Arrange
    u = user2_1
    session.add(u)
    session.commit()

    # Act
    u.aliases.append("qux")
    session.commit()

    # Assert
    assert isinstance(u.aliases, MutableList)
    assert u.aliases == ["bar", "baz", "qux"]


def test_nested_mutable_list_stored_as_jsonb(session: Session, user2_2: User):

    # Arrange - aliases is None, so should default
    u = user2_2

    # Act
    session.add(u)
    session.commit()

    # Assert
    assert isinstance(u.aliases, MutableList)
    assert len(u.aliases) == 0
    assert u.schedule == [["meeting", "launch"], ["training", "presentation"]]


def test_nested_mutable_list_stored_as_jsonb_mutation_top_level(session: Session, user2_2: User):

    # Assert - aliases is None, so should default
    u = user2_2
    session.add(u)
    session.commit()

    # Act - Mutation at top level
    u.schedule.append(["breakfast", "consulting"])
    session.commit()

    # Assert
    assert isinstance(u.aliases, MutableList)
    assert len(u.aliases) == 0
    assert u.schedule == [["meeting", "launch"], ["training", "presentation"], ["breakfast", "consulting"]]


def test_nested_mutable_list_stored_as_jsonb_mutation_nested_level(session: Session):

    # Assert - aliases is None, so should default
    u = UserV2(name="foo", schedule=[["meeting", "launch"], ["training", "presentation"], ["breakfast", "consulting"]])
    session.add(u)
    session.commit()

    # Act - Mutation at top level
    u.schedule[0].insert(0, "breakfast")
    session.commit()

    # Assert
    assert isinstance(u.aliases, MutableList)
    assert len(u.aliases) == 0
    assert u.schedule == [
        ["breakfast", "meeting", "launch"],
        ["training", "presentation"],
        ["breakfast", "consulting"],
    ]


def test_nested_mutable_list_stored_as_jsonb_mutation_nested_level_pop(session: Session):

    # Assert - aliases is None, so should default
    u = UserV2(
        name="foo",
        schedule=[["breakfast", "meeting", "launch"], ["training", "presentation"], ["breakfast", "consulting"]],
    )
    session.add(u)
    session.commit()

    # Act - Pop off bottom of list
    u.schedule.pop()
    session.commit()

    # Assert
    assert u.schedule == [["breakfast", "meeting", "launch"], ["training", "presentation"]]


def test_mutable_list_mixed_with_dict(session: Session):

    # Arrange
    u = UserV2(
        name="foo",
        schedule=[
            {"day": "mon", "events": ["meeting", "launch"]},
            {"day": "tue", "events": ["training", "presentation"]},
        ],
    )

    # Act - add/commit
    session.add(u)
    session.commit()

    # Assert
    assert isinstance(u.schedule, MutableList)
    assert isinstance(u.schedule[0], TrackedDict)
    assert isinstance(u.schedule[0]["events"], TrackedList)


def test_mutable_list_mixed_with_dict_insert(session: Session):

    # Arrange
    u = UserV2(
        name="foo",
        schedule=[
            {"day": "mon", "events": ["meeting", "launch"]},
            {"day": "tue", "events": ["training", "presentation"]},
        ],
    )
    session.add(u)
    session.commit()

    # Act - insert into nested list
    u.schedule[0]["events"].insert(0, "breakfast")
    session.commit()

    # Assert
    assert u.schedule[0] == {"day": "mon", "events": ["breakfast", "meeting", "launch"]}
    assert u.schedule[1] == {"day": "tue", "events": ["training", "presentation"]}


def test_mutable_list_stored_as_jsonb_and_nullable(session: Session):

    # Arrange
    u = UserV3(name="foo", aliases=["bar", "baz"])

    # Act - add/commit
    session.add(u)
    session.commit()

    # Assert
    assert isinstance(u.aliases, MutableList)
    assert u.aliases == ["bar", "baz"]
    assert u.schedule is None


def test_mutable_list_stored_as_jsonb_and_nullable_append(session: Session):

    # Arrange
    u = UserV3(name="foo")
    u.aliases = MutableList(["bar", "baz"])

    session.add(u)
    session.commit()

    # Act - append
    u.aliases.append("qux")
    session.commit()

    # Assert
    assert isinstance(u.aliases, MutableList)
    assert u.aliases == ["bar", "baz", "qux"]
    assert u.schedule is None


def test_mutable_list_stored_as_jsonb_and_nullable_add(session: Session):

    # Arrange
    u = UserV3(name="foo")
    u.aliases = MutableList(["bar", "baz", "qux"])
    u.schedule = MutableList([["breakfast", "meeting", "launch"], ["training", "presentation"]])

    # Act - add/commit
    session.add(u)
    session.commit()

    # Act
    assert u.aliases == ["bar", "baz", "qux"]
    assert u.schedule == [["breakfast", "meeting", "launch"], ["training", "presentation"]]


def test_nested_mutable_list_stored_as_jsonb_and_nullable(session: Session):

    # Arrange
    u = UserV3(name="foo", schedule=[["meeting", "launch"], ["training", "presentation"]])
    session.add(u)
    session.commit()

    # Act - Pop
    s = u.schedule
    assert s is not None
    s.pop()
    session.commit()

    # Assert
    assert u.aliases is None
    assert u.schedule == [["meeting", "launch"]]


def test_nested_mutable_list_stored_as_jsonb_and_nullable_and_mutate(session: Session):

    # Arrange
    u = UserV3(name="foo")
    u.schedule = MutableList([["meeting", "launch"], ["training", "presentation"]])
    session.add(u)
    session.commit()

    # Act - append
    s = u.schedule
    s.append(["breakfast", "consulting"])
    session.commit()

    # Assert
    assert u.aliases is None
    assert u.schedule == [["meeting", "launch"], ["training", "presentation"], ["breakfast", "consulting"]]


def test_nested_mutable_list_stored_as_jsonb_and_nullable_and_mutate_nested_level(session: Session):

    # Arrange
    u = UserV3(name="foo")
    u.schedule = MutableList([["meeting", "launch"], ["training", "presentation"], ["breakfast", "consulting"]])
    session.add(u)
    session.commit()

    # Act - Mutation at nested level
    s = u.schedule
    s[0].insert(0, "wakeup")

    session.commit()

    # Assert
    assert s == [
        ["wakeup", "meeting", "launch"],
        ["training", "presentation"],
        ["breakfast", "consulting"],
    ]


def test_nested_mutable_list_stored_as_jsonb_and_nullable_and_mutate_within_nested(session: Session):

    # Arrange
    u = UserV3(name="foo")
    u.schedule = MutableList([["meeting", "launch"], ["training", "presentation"], ["breakfast", "consulting"]])
    session.add(u)
    session.commit()

    # Act - Mutation within nested level
    s = u.schedule
    s[0][0] = "new meeting"

    session.commit()

    # Assert
    assert s == [
        ["new meeting", "launch"],
        ["training", "presentation"],
        ["breakfast", "consulting"],
    ]
