from typing import List
from typing import Optional

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Session
from sqlalchemyv2_nested_mutable import MutablePydanticBaseModel
from sqlalchemyv2_nested_mutable._compat import pydantic


class Base(DeclarativeBase):
    pass


class Addresses(MutablePydanticBaseModel):
    class AddressItem(pydantic.BaseModel):
        street: str
        city: str
        area: Optional[str]

    work: List[AddressItem] = []
    home: List[AddressItem] = []


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(30))
    addresses_default: Mapped[Optional[Addresses]] = mapped_column(Addresses.as_mutable())
    addresses_json: Mapped[Optional[Addresses]] = mapped_column(Addresses.as_mutable(JSON()))
    addresses_jsonb: Mapped[Optional[Addresses]] = mapped_column(Addresses.as_mutable(JSONB()))


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
