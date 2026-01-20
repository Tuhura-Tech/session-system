from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy.types import Integer, TypeDecorator

TIntEnum = TypeVar("TIntEnum")


class IntEnumType(TypeDecorator[int]):
    """Store an IntEnum as an INTEGER in the DB.

    This keeps the DB column as an int (easy to query) while letting Python code
    work with an Enum for readability and safety.
    """

    impl = Integer
    cache_ok = True

    def __init__(self, enum_class: type[TIntEnum]) -> None:
        super().__init__()
        self._enum_class = enum_class

    def process_bind_param(self, value: Any, dialect: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except Exception as exc:
            raise TypeError(f"Invalid value for {self._enum_class.__name__}: {value!r}") from exc

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return self._enum_class(int(value))
