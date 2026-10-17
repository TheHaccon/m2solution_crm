from sqlalchemy.orm import Session

from app.models.file import FileKind, FileNode, FileSpace
from app.seeds.context import DevSeedContext
from app.services.file_storage import get_storage


def seed_demo_files(db: Session, ctx: DevSeedContext) -> None:
    if ctx.main_team is None or ctx.primary_user is None:
        return
    user = ctx.primary_user
    storage = get_storage()

    team_configs = FileNode(
        kind=FileKind.folder.value,
        name="configs",
        parent_id=None,
        space=FileSpace.team.value,
        team_id=ctx.main_team.id,
        owner_id=None,
        created_by_id=user.id,
    )
    db.add(team_configs)
    db.flush()

    readme_key = storage.new_key()
    readme_body = b"# Team config\n\nDev seed markdown file in team space.\n"
    storage.put(readme_key, readme_body)
    db.add(
        FileNode(
            kind=FileKind.file.value,
            name="README.md",
            parent_id=team_configs.id,
            space=FileSpace.team.value,
            team_id=ctx.main_team.id,
            owner_id=None,
            storage_key=readme_key,
            mime_type="text/markdown",
            size_bytes=len(readme_body),
            created_by_id=user.id,
        )
    )

    notes_key = storage.new_key()
    notes_body = b"Personal dev seed notes.\n"
    storage.put(notes_key, notes_body)
    db.add(
        FileNode(
            kind=FileKind.file.value,
            name="dev-notes.txt",
            parent_id=None,
            space=FileSpace.personal.value,
            team_id=None,
            owner_id=user.id,
            storage_key=notes_key,
            mime_type="text/plain",
            size_bytes=len(notes_body),
            created_by_id=user.id,
        )
    )
