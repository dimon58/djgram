# ruff: noqa
import pydantic
import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemyv2_nested_mutable import MutablePydanticBaseModel


class Base(DeclarativeBase):
    pass


class Addresses(MutablePydanticBaseModel):
    class AddressItem(pydantic.BaseModel):
        street: str
        city: str
        area: str | None

    work: list[AddressItem] = []
    home: list[AddressItem] = []


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(30))
    addresses_default: Mapped[Addresses | None] = mapped_column(Addresses.as_mutable())
    addresses_json: Mapped[Addresses | None] = mapped_column(Addresses.as_mutable(JSON()))
    addresses_jsonb: Mapped[Addresses | None] = mapped_column(Addresses.as_mutable(JSONB()))


@pytest.fixture(scope="module", autouse=True)
def mapper():
    return Base


def test_mutable_pydantic_type(session: Session):

    # Arrange
    u = User(name="foo")

    # Act
    session.add(u)
    session.commit()

    # Assert
    assert session.scalar(sa.select(sa.func.pg_typeof(User.addresses_default))) == "jsonb"
    assert session.scalar(sa.select(sa.func.pg_typeof(User.addresses_json))) == "json"
    assert session.scalar(sa.select(sa.func.pg_typeof(User.addresses_jsonb))) == "jsonb"
