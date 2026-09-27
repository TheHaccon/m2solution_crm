from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminPasswordResetRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str

    model_config = {"from_attributes": True}
