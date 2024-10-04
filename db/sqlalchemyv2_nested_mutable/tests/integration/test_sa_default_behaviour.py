# ruff: noqa
import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(30))
    aliases: Mapped[list[str]] = mapped_column(ARRAY(sa.String(128)))
    addresses: Mapped[dict] = mapped_column(JSONB(), default=dict)


@pytest.fixture(scope="module", autouse=True)
def mapper():
    return Base


def test_sa_array_not_mutable(session: Session):
    """
    Test: Demonstrates/tests default SAv2 behaviour for array serialization
    """

    # Arrange
    u = User(name="foo", aliases=["bar", "baz"])
    session.add(u)
    session.commit()

    # Act
    u.aliases.append("qux")
    session.commit()

    # Assert - even though we appended qux, the default SAv2 code would ignore the change
    assert u.aliases == ["bar", "baz"]


def test_sa_jsonb_not_mutable(session: Session):
    """
    Test: Demonstrates/tests default SAv2 behaviour for JSON serialization
    """

    # Arrange
    u = User(name="bar", aliases=["baz", "qux"], addresses={"home": "bar", "work": "baz", "email": "xyz@example.com"})
    session.add(u)
    session.commit()

    # Act
    u.addresses["email"] = "abc@example.com"
    assert u.addresses["email"] == "abc@example.com"
    session.commit()

    # Assert - even though we amended the email, the default SAv2 code would ignore the change
    assert u.addresses["email"] == "xyz@example.com"
