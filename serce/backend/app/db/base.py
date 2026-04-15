from enum import Enum as PyEnum

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def enum_values(enum_cls: type[PyEnum]) -> list[str]:
    """values_callable for sa.Enum — store .value (not .name) in DB.

    Required for `(str, enum.Enum)` classes whose value differs from name
    (e.g. UserStatus.ACTIVE = "active"). Without this, asyncpg raises
    InvalidTextRepresentationError when name ≠ any postgres enum label.
    """
    return [m.value for m in enum_cls]
