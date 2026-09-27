from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import utcnow


class FileKind(str, Enum):
    folder = "folder"
    file = "file"


class FileSpace(str, Enum):
    team = "team"
    personal = "personal"


class FileNode(Base):
    __tablename__ = "file_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), index=True)
    name: Mapped[str] = mapped_column(String(255))
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("file_nodes.id", ondelete="CASCADE"), nullable=True, index=True
    )
    space: Mapped[str] = mapped_column(String(16), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    storage_key: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(127), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_backend: Mapped[str] = mapped_column(String(16), default="local")
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    parent: Mapped["FileNode | None"] = relationship(
        remote_side="FileNode.id",
        back_populates="children",
    )
    children: Mapped[list["FileNode"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
    )


Index(
    "uq_file_nodes_sibling_name",
    FileNode.space,
    func.coalesce(FileNode.team_id, 0),
    func.coalesce(FileNode.owner_id, 0),
    func.coalesce(FileNode.parent_id, 0),
    FileNode.name,
    unique=True,
)
