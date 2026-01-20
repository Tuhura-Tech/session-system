from pydantic import BaseModel


class ApiError(BaseModel):
    """Standard API error response."""

    error: str
    detail: str | None = None
