from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class UserCreateResponse(BaseModel):
    name: str
    public_key: str
    private_key: str
