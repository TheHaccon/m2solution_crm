from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.seeds.context import DevSeedContext


def seed_demo_meetings(db: Session, ctx: DevSeedContext) -> None:
    if not ctx.clients:
        return
    acme = ctx.clients[0]
    north = ctx.clients[1] if len(ctx.clients) > 1 else acme
    rows = [
        Meeting(
            client_id=acme.id,
            title="Kickoff — Acme",
            scheduled_at=datetime(ctx.seed_year, 3, 12, 15, 0, tzinfo=timezone.utc),
            attendees="Mat, Client PM",
            body="# Kickoff\n\n- Scope agreed\n- **Next:** send draft invoice",
        ),
        Meeting(
            client_id=north.id,
            title="Support check-in",
            scheduled_at=datetime(ctx.seed_year, 6, 4, 18, 30, tzinfo=timezone.utc),
            attendees="Mathieu",
            body="Plain notes without headings.\nFollow up on hosting renewal.",
        ),
    ]
    for row in rows:
        db.add(row)
