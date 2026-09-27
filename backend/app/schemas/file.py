from datetime import datetime

from pydantic import BaseModel, Field


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    parent_id: int | None = None
    space: str = Field(pattern="^(team|personal)$")


class TextFileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    parent_id: int | None = None
    space: str = Field(pattern="^(team|personal)$")
    content: str = ""


class FileNodeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    parent_id: int | None = None


class FileContentPut(BaseModel):
    content: str


class FileNodeOut(BaseModel):
    id: int
    kind: str
    name: str
    parent_id: int | None
    space: str
    mime_type: str | None
    size_bytes: int | None
    storage_backend: str
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
