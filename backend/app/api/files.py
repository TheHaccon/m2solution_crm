from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, require_team_member
from app.models.file import FileKind, FileNode, FileSpace
from app.models.user import User, utcnow
from app.schemas.file import FileContentPut, FileNodeOut, FileNodeUpdate, FolderCreate, TextFileCreate
from app.services.file_storage import get_storage
from app.services.invoice_files import ensure_personal_invoices_folder
from app.services.expense_files import ensure_all_category_folders
from app.services.expenses import seed_categories


router = APIRouter(prefix="/api/files", tags=["files"])

TEXT_EXTS = {
    ".txt",
    ".md",
    ".markdown",
    ".json",
    ".csv",
    ".yml",
    ".yaml",
    ".xml",
    ".ini",
    ".cfg",
    ".conf",
    ".log",
    ".env",
    ".html",
    ".css",
    ".js",
    ".ts",
}
MIME_BY_EXT = {
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".json": "application/json",
    ".yml": "text/yaml",
    ".yaml": "text/yaml",
}


def sanitize_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned or cleaned in {".", ".."}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid name")
    if "/" in cleaned or "\\" in cleaned or "\x00" in cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid name")
    if len(cleaned) > 255:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name too long")
    return cleaned


def guess_mime(name: str, fallback: str | None = None) -> str:
    ext = Path(name).suffix.lower()
    if ext in MIME_BY_EXT:
        return MIME_BY_EXT[ext]
    guessed, _ = mimetypes.guess_type(name)
    return guessed or fallback or "application/octet-stream"


def is_text_file(node: FileNode) -> bool:
    if node.kind != FileKind.file.value:
        return False
    mime = (node.mime_type or "").lower()
    if mime.startswith("text/") or mime in {
        "application/json",
        "application/xml",
        "application/x-yaml",
        "text/yaml",
    }:
        return True
    return Path(node.name).suffix.lower() in TEXT_EXTS


def parse_space(value: str) -> str:
    if value not in {FileSpace.team.value, FileSpace.personal.value}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="space must be team or personal")
    return value


def space_scope(
    db: Session,
    user: User,
    space: str,
    x_team_id: int | None,
) -> tuple[int | None, int | None]:
    space = parse_space(space)
    if space == FileSpace.personal.value:
        return None, user.id
    if x_team_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Team-Id header is required")
    require_team_member(db, x_team_id, user.id)
    return x_team_id, None


def load_accessible(
    db: Session,
    node_id: int,
    user: User,
    x_team_id: int | None,
) -> FileNode:
    node = db.get(FileNode, node_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if node.space == FileSpace.personal.value:
        if node.owner_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return node
    if x_team_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    require_team_member(db, x_team_id, user.id)
    if node.team_id != x_team_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return node


def load_parent(
    db: Session,
    parent_id: int | None,
    user: User,
    space: str,
    team_id: int | None,
    owner_id: int | None,
    x_team_id: int | None,
) -> FileNode | None:
    if parent_id is None:
        return None
    parent = load_accessible(db, parent_id, user, x_team_id)
    if parent.kind != FileKind.folder.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent must be a folder")
    if parent.space != space or parent.team_id != team_id or parent.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return parent


def is_under(db: Session, node: FileNode, maybe_descendant: FileNode) -> bool:
    current: FileNode | None = maybe_descendant
    seen: set[int] = set()
    while current is not None:
        if current.id == node.id:
            return True
        if current.id in seen:
            break
        seen.add(current.id)
        current = db.get(FileNode, current.parent_id) if current.parent_id else None
    return False


def descendants(db: Session, root: FileNode) -> list[FileNode]:
    found: list[FileNode] = []
    queue = [root]
    while queue:
        node = queue.pop()
        kids = list(db.scalars(select(FileNode).where(FileNode.parent_id == node.id)))
        found.extend(kids)
        queue.extend(kids)
    return found


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A file or folder with that name already exists here",
        )


def new_folder(
    *,
    name: str,
    parent_id: int | None,
    space: str,
    team_id: int | None,
    owner_id: int | None,
    user: User,
) -> FileNode:
    return FileNode(
        kind=FileKind.folder.value,
        name=name,
        parent_id=parent_id,
        space=space,
        team_id=team_id,
        owner_id=owner_id,
        storage_backend="local",
        created_by_id=user.id,
    )


def new_file(
    *,
    name: str,
    parent_id: int | None,
    space: str,
    team_id: int | None,
    owner_id: int | None,
    user: User,
    storage_key: str,
    mime_type: str,
    size_bytes: int,
) -> FileNode:
    return FileNode(
        kind=FileKind.file.value,
        name=name,
        parent_id=parent_id,
        space=space,
        team_id=team_id,
        owner_id=owner_id,
        storage_key=storage_key,
        mime_type=mime_type,
        size_bytes=size_bytes,
        storage_backend="local",
        created_by_id=user.id,
    )


@router.get("", response_model=list[FileNodeOut])
def list_files(
    space: Literal["team", "personal"] = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    x_team_id: Annotated[int | None, Header()] = None,
) -> list[FileNode]:
    team_id, owner_id = space_scope(db, user, space, x_team_id)
    stmt = select(FileNode).where(FileNode.space == space)
    if space == FileSpace.team.value:
        stmt = stmt.where(FileNode.team_id == team_id)
    else:
        ensure_personal_invoices_folder(db, user)
        seed_categories(db, user)
        ensure_all_category_folders(db, user)
        db.commit()
        stmt = stmt.where(FileNode.owner_id == owner_id)
    stmt = stmt.order_by(FileNode.kind.desc(), FileNode.name)
    return list(db.scalars(stmt).all())


@router.post("/folders", response_model=FileNodeOut, status_code=status.HTTP_201_CREATED)
def create_folder(
    body: FolderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    x_team_id: Annotated[int | None, Header()] = None,
) -> FileNode:
    space = parse_space(body.space)
    team_id, owner_id = space_scope(db, user, space, x_team_id)
    load_parent(db, body.parent_id, user, space, team_id, owner_id, x_team_id)
    node = new_folder(
        name=sanitize_name(body.name),
        parent_id=body.parent_id,
        space=space,
        team_id=team_id,
        owner_id=owner_id,
        user=user,
    )
    db.add(node)
    commit_or_conflict(db)
    db.refresh(node)
    return node


@router.post("/text", response_model=FileNodeOut, status_code=status.HTTP_201_CREATED)
def create_text_file(
    body: TextFileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    x_team_id: Annotated[int | None, Header()] = None,
) -> FileNode:
    space = parse_space(body.space)
    team_id, owner_id = space_scope(db, user, space, x_team_id)
    load_parent(db, body.parent_id, user, space, team_id, owner_id, x_team_id)
    data = body.content.encode("utf-8")
    if len(data) > settings.files_max_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 25 MB)")
    name = sanitize_name(body.name)
    storage = get_storage()
    key = storage.new_key()
    storage.put(key, data)
    node = new_file(
        name=name,
        parent_id=body.parent_id,
        space=space,
        team_id=team_id,
        owner_id=owner_id,
        user=user,
        storage_key=key,
        mime_type=guess_mime(name, "text/plain"),
        size_bytes=len(data),
    )
    db.add(node)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        storage.delete(key)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A file or folder with that name already exists here",
        )
    db.refresh(node)
    return node


@router.post("/upload", response_model=FileNodeOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    space: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    parent_id: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    x_team_id: Annotated[int | None, Header()] = None,
) -> FileNode:
    space = parse_space(space)
    team_id, owner_id = space_scope(db, user, space, x_team_id)
    parsed_parent = int(parent_id) if parent_id not in (None, "") else None
    load_parent(db, parsed_parent, user, space, team_id, owner_id, x_team_id)
    name = sanitize_name(file.filename or "upload")
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > settings.files_max_bytes:
            raise HTTPException(
                status_code=413,
                detail="File too large (max 25 MB)",
            )
        chunks.append(chunk)
    data = b"".join(chunks)
    storage = get_storage()
    key = storage.new_key()
    storage.put(key, data)
    node = new_file(
        name=name,
        parent_id=parsed_parent,
        space=space,
        team_id=team_id,
        owner_id=owner_id,
        user=user,
        storage_key=key,
        mime_type=guess_mime(name, file.content_type),
        size_bytes=len(data),
    )
    db.add(node)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        storage.delete(key)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A file or folder with that name already exists here",
        )
    db.refresh(node)
    return node


@router.get("/{node_id}", response_model=FileNodeOut)
def get_file(
    node_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    x_team_id: Annotated[int | None, Header()] = None,
) -> FileNode:
    return load_accessible(db, node_id, user, x_team_id)


@router.get("/{node_id}/content")
def get_content(
    node_id: int,
    download: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    x_team_id: Annotated[int | None, Header()] = None,
) -> Response:
    node = load_accessible(db, node_id, user, x_team_id)
    if node.kind != FileKind.file.value or not node.storage_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a file")
    path = get_storage().path_for(node.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File data missing")
    disposition = "attachment" if download else "inline"
    return FileResponse(
        path,
        media_type=node.mime_type or "application/octet-stream",
        filename=node.name,
        content_disposition_type=disposition,
    )


@router.put("/{node_id}/content", response_model=FileNodeOut)
def put_content(
    node_id: int,
    body: FileContentPut,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    x_team_id: Annotated[int | None, Header()] = None,
) -> FileNode:
    node = load_accessible(db, node_id, user, x_team_id)
    if node.kind != FileKind.file.value or not node.storage_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a file")
    if not is_text_file(node):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only text files can be edited")
    data = body.content.encode("utf-8")
    if len(data) > settings.files_max_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 25 MB)")
    get_storage().put(node.storage_key, data)
    node.size_bytes = len(data)
    node.updated_at = utcnow()
    db.commit()
    db.refresh(node)
    return node


@router.patch("/{node_id}", response_model=FileNodeOut)
def update_file(
    node_id: int,
    body: FileNodeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    x_team_id: Annotated[int | None, Header()] = None,
) -> FileNode:
    node = load_accessible(db, node_id, user, x_team_id)
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        node.name = sanitize_name(data["name"])
        if node.kind == FileKind.file.value:
            node.mime_type = guess_mime(node.name, node.mime_type)
    if "parent_id" in data:
        new_parent_id = data["parent_id"]
        parent = load_parent(db, new_parent_id, user, node.space, node.team_id, node.owner_id, x_team_id)
        if parent is not None and is_under(db, node, parent):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot move a folder into itself")
        node.parent_id = new_parent_id
    node.updated_at = utcnow()
    commit_or_conflict(db)
    db.refresh(node)
    return node


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    node_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    x_team_id: Annotated[int | None, Header()] = None,
) -> None:
    node = load_accessible(db, node_id, user, x_team_id)
    storage = get_storage()
    to_delete = [node, *descendants(db, node)]
    keys = [n.storage_key for n in to_delete if n.kind == FileKind.file.value and n.storage_key]
    db.delete(node)
    db.commit()
    for key in keys:
        storage.delete(key)
