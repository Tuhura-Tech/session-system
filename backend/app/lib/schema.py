from typing import Any

import msgspec
from advanced_alchemy.utils.text import camelize
from pydantic import BaseModel
from pydantic import ConfigDict

# class CamelizedBaseStruct(BaseModel, rename="camel"):
#     """Camelized Base Struct"""


class BaseSchema(BaseModel):
    """Base Settings."""

    model_config = ConfigDict(
        validate_assignment=True,
        from_attributes=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
    )


class CamelizedBaseSchema(BaseSchema):
    """Camelized Base pydantic schema."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=camelize)
