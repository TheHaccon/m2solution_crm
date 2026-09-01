from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class TeamMemberAdd(BaseModel):
    email: EmailStr


class TeamMemberOut(BaseModel):
    user_id: int
    email: str
    full_name: str


class TeamOut(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamDetailOut(TeamOut):
    members: list[TeamMemberOut]
