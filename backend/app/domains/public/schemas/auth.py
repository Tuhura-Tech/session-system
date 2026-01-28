from pydantic import BaseModel, EmailStr, Field


class MagicLinkRequest(BaseModel):
    email: EmailStr
    return_to: str | None = Field(None, alias="returnTo")


class MagicLinkRequestResponse(BaseModel):
    ok: bool = True
    # Only returned in debug mode to make local/dev flows and tests easier.
    debug_token: str | None = Field(None, alias="debugToken")


class LogoutResponse(BaseModel):
    ok: bool = True
