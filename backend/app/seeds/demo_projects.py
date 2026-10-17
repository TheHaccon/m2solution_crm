from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.project import Project, TimeEntry
from app.seeds.context import DevSeedContext
from app.services.project_time import SOURCE_MANUAL, SOURCE_TIMER


def seed_demo_projects(db: Session, ctx: DevSeedContext) -> None:
    if ctx.main_team is None or ctx.primary_user is None:
        return
    user = ctx.primary_user
    names = ["Website refresh", "Internal tooling"]
    ctx.projects = []
    for name in names:
        project = Project(team_id=ctx.main_team.id, name=name)
        db.add(project)
        db.flush()
        ctx.projects.append(project)

    website, tooling = ctx.projects[0], ctx.projects[1]
    now = datetime.now(timezone.utc)

    db.add(
        TimeEntry(
            user_id=user.id,
            project_id=website.id,
            source=SOURCE_MANUAL,
            work_date=date(ctx.seed_year, 8, 12),
            duration_seconds=3600,
            segment_started_at=None,
            ended_at=now,
            note="Dev seed manual entry",
        )
    )
    db.add(
        TimeEntry(
            user_id=user.id,
            project_id=website.id,
            source=SOURCE_TIMER,
            work_date=None,
            duration_seconds=900,
            segment_started_at=None,
            ended_at=now,
            note="Dev seed completed timer segment",
        )
    )
    db.add(
        TimeEntry(
            user_id=user.id,
            project_id=tooling.id,
            source=SOURCE_TIMER,
            work_date=None,
            duration_seconds=120,
            segment_started_at=now,
            ended_at=None,
            note=None,
        )
    )
