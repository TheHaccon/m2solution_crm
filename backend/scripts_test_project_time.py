"""Staff projects and personal time checks (issues #19–#22).

Uses an in-memory SQLite database. Startup is patched so the app lifespan
does not open DATABASE_URL.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.project import Project, TimeEntry
from app.models.team import Team, TeamMember
from app.models.user import User

PROJECT_KEYS = {
    "id",
    "name",
    "created_at",
    "updated_at",
    "my_finished_seconds",
    "server_now",
    "server_today",
    "my_session",
}
SESSION_KEYS = {
    "id",
    "project_id",
    "status",
    "accumulated_seconds",
    "segment_started_at",
    "server_now",
}
ENTRY_KEYS = {
    "id",
    "project_id",
    "source",
    "work_date",
    "duration_seconds",
    "note",
    "ended_at",
}


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 10, 7, 2, 30, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now = self.now + timedelta(seconds=seconds)


def must(response, code: int):  # type: ignore[no-untyped-def]
    if response.status_code != code:
        raise AssertionError(f"expected {code}, got {response.status_code}: {response.text}")
    return response


def headers(token: str, team_id: int | None = None) -> dict[str, str]:
    data = {"Authorization": f"Bearer {token}"}
    if team_id is not None:
        data["X-Team-Id"] = str(team_id)
    return data


def main() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    tables = [User.__table__, Team.__table__, TeamMember.__table__, Project.__table__, TimeEntry.__table__]
    Base.metadata.create_all(bind=engine, tables=tables)
    SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    db = SessionFactory()
    try:
        user_a = User(email="time-a@example.com", password_hash="x", full_name="A")
        user_b = User(email="time-b@example.com", password_hash="x", full_name="B")
        team_a = Team(name="Team A")
        team_b = Team(name="Team B")
        db.add_all([user_a, user_b, team_a, team_b])
        db.flush()
        db.add_all(
            [
                TeamMember(team_id=team_a.id, user_id=user_a.id),
                TeamMember(team_id=team_b.id, user_id=user_a.id),
                TeamMember(team_id=team_a.id, user_id=user_b.id),
            ]
        )
        db.commit()
        user_a_id, user_b_id = user_a.id, user_b.id
        team_a_id, team_b_id = team_a.id, team_b.id
    finally:
        db.close()

    token_a = create_access_token(str(user_a_id))
    token_b = create_access_token(str(user_b_id))
    auth_a = headers(token_a, team_a_id)
    auth_b = headers(token_b, team_a_id)
    auth_a_b = headers(token_a, team_b_id)

    def project_rows(project_id: int) -> list[TimeEntry]:
        session = SessionFactory()
        try:
            return list(session.scalars(select(TimeEntry).where(TimeEntry.project_id == project_id).order_by(TimeEntry.id)).all())
        finally:
            session.close()

    def running_ids(user_id: int) -> list[int]:
        session = SessionFactory()
        try:
            rows = session.scalars(
                select(TimeEntry).where(
                    TimeEntry.user_id == user_id,
                    TimeEntry.segment_started_at.is_not(None),
                    TimeEntry.ended_at.is_(None),
                )
            ).all()
            return [row.id for row in rows]
        finally:
            session.close()

    def entry_row(entry_id: int) -> TimeEntry | None:
        session = SessionFactory()
        try:
            return session.get(TimeEntry, entry_id)
        finally:
            session.close()

    clock = Clock()

    def refuse_app_db(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("project time tests must not open the application database")

    def override_get_db():
        session = SessionFactory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with (
            patch("app.main.seed_staff", lambda: None),
            patch.object(Base.metadata, "create_all", lambda *a, **k: None),
            patch("app.core.database.engine.connect", refuse_app_db),
            patch("app.services.project_time.utcnow", clock),
            TestClient(app) as client,
        ):
            _run(
                client,
                clock,
                auth_a,
                auth_b,
                auth_a_b,
                token_a,
                team_b_id,
                user_a_id,
                user_b_id,
                project_rows,
                running_ids,
                entry_row,
                SessionFactory,
            )
    finally:
        app.dependency_overrides.clear()

    print("project time checks passed")


def _run(  # type: ignore[no-untyped-def]
    client,
    clock: Clock,
    auth_a,
    auth_b,
    auth_a_b,
    token_a,
    team_b_id,
    user_a_id,
    user_b_id,
    project_rows,
    running_ids,
    entry_row,
    SessionFactory,
) -> None:
    missing_token = client.get("/api/projects")
    must(missing_token, 401)

    missing_team = client.get("/api/projects", headers=headers(token_a))
    must(missing_team, 400)

    must(client.get("/api/projects", headers=headers(token_a, 99999)), 403)
    must(client.get("/api/projects", headers={"Authorization": auth_b["Authorization"], "X-Team-Id": str(team_b_id)}), 403)

    created = must(client.post("/api/projects", headers=auth_a, json={"name": "  Zulu  ", "client_id": 1}), 201)
    body = created.json()
    assert set(body.keys()) == PROJECT_KEYS
    assert "client_id" not in body
    assert body["name"] == "Zulu"
    assert body["my_finished_seconds"] == 0
    assert body["my_session"] is None
    assert body["server_today"] == "2026-10-07"
    zulu_id = body["id"]

    duplicate = must(client.post("/api/projects", headers=auth_a, json={"name": "Zulu"}), 201)
    assert duplicate.json()["id"] != zulu_id
    assert duplicate.json()["name"] == "Zulu"

    alpha = must(client.post("/api/projects", headers=auth_a, json={"name": "Alpha"}), 201).json()
    alpha_again = must(client.post("/api/projects", headers=auth_a, json={"name": "Alpha"}), 201).json()
    long_name = must(client.post("/api/projects", headers=auth_a, json={"name": "N" * 255}), 201).json()
    must(client.post("/api/projects", headers=auth_a, json={"name": "N" * 256}), 422)
    for blank in ("", "   ", "\n\t"):
        must(client.post("/api/projects", headers=auth_a, json={"name": blank}), 422)

    secret = must(client.post("/api/projects", headers=auth_a_b, json={"name": "Secret"}), 201).json()
    listed = must(client.get("/api/projects", headers=auth_a), 200).json()
    listed_names = [row["name"] for row in listed]
    assert "Secret" not in listed_names
    assert listed_names.count("Alpha") == 2
    alpha_positions = [row for row in listed if row["name"] == "Alpha"]
    assert [row["id"] for row in alpha_positions] == sorted(row["id"] for row in alpha_positions)
    assert listed_names.index("Alpha") < listed_names.index("Zulu")
    assert any(row["id"] == zulu_id and row["my_finished_seconds"] == 0 for row in listed)
    zulu_positions = [i for i, row in enumerate(listed) if row["name"] == "Zulu"]
    assert zulu_positions == sorted(zulu_positions)
    assert [listed[i]["id"] for i in zulu_positions] == sorted(listed[i]["id"] for i in zulu_positions)

    must(client.get(f"/api/projects/{secret['id']}", headers=auth_a), 404)
    must(client.patch(f"/api/projects/{secret['id']}", headers=auth_a, json={"name": "Stolen"}), 404)
    still_secret = must(client.get(f"/api/projects/{secret['id']}", headers=auth_a_b), 200).json()
    assert still_secret["name"] == "Secret"
    assert "client_id" not in still_secret

    other_team_list = must(client.get("/api/projects", headers=auth_b), 200).json()
    assert secret["id"] not in {row["id"] for row in other_team_list}
    assert alpha["id"] in {row["id"] for row in other_team_list}

    must(client.delete(f"/api/projects/{alpha['id']}", headers=auth_a), 405)
    after_delete = must(client.get(f"/api/projects/{alpha['id']}", headers=auth_a), 200).json()
    assert after_delete["name"] == "Alpha"

    renamed = must(client.patch(f"/api/projects/{alpha['id']}", headers=auth_b, json={"name": "  Alpha v2  "}), 200).json()
    assert renamed["name"] == "Alpha v2"
    assert must(client.get("/api/projects", headers=auth_a), 200).json()
    seen = must(client.get("/api/projects", headers=auth_a), 200).json()
    assert any(row["id"] == alpha["id"] and row["name"] == "Alpha v2" for row in seen)

    # Finished entries. Omitted date uses the server UTC date (2026-10-07), not a laptop date.
    omitted = must(
        client.post(f"/api/projects/{alpha['id']}/entries", headers=auth_a, json={"duration_seconds": 90, "note": "  alpha-private  "}),
        201,
    ).json()
    assert set(omitted.keys()) == ENTRY_KEYS
    assert omitted["source"] == "manual"
    assert omitted["work_date"] == "2026-10-07"
    assert omitted["duration_seconds"] == 90
    assert omitted["note"] == "alpha-private"
    assert omitted["project_id"] == alpha["id"]

    explicit_null = must(
        client.post(
            f"/api/projects/{alpha['id']}/entries",
            headers=auth_a,
            json={"work_date": None, "duration_seconds": 30, "note": "   "},
        ),
        201,
    ).json()
    assert explicit_null["work_date"] == "2026-10-07"
    assert explicit_null["note"] is None

    dated = must(
        client.post(
            f"/api/projects/{alpha['id']}/entries",
            headers=auth_a,
            json={"work_date": "2026-01-15", "duration_seconds": 15, "note": "dated"},
        ),
        201,
    ).json()
    assert dated["work_date"] == "2026-01-15"

    zero = client.post(f"/api/projects/{alpha['id']}/entries", headers=auth_a, json={"duration_seconds": 0})
    must(zero, 422)
    assert "duration must be greater than zero" in zero.text
    must(client.post(f"/api/projects/{alpha['id']}/entries", headers=auth_a, json={"duration_seconds": -4}), 422)

    teammate = must(
        client.post(
            f"/api/projects/{alpha['id']}/entries",
            headers=auth_b,
            json={"duration_seconds": 50, "note": "beta-private"},
        ),
        201,
    ).json()

    mine = must(client.get(f"/api/projects/{alpha['id']}/entries", headers=auth_a), 200).json()
    assert isinstance(mine, list)
    assert all(set(row.keys()) == ENTRY_KEYS for row in mine)
    assert "beta-private" not in client.get(f"/api/projects/{alpha['id']}/entries", headers=auth_a).text
    assert {row["id"] for row in mine} >= {omitted["id"], explicit_null["id"], dated["id"]}
    assert teammate["id"] not in {row["id"] for row in mine}
    ended_pairs = [(row["ended_at"], row["id"]) for row in mine]
    assert ended_pairs == sorted(ended_pairs, reverse=True)

    project_after = must(client.get(f"/api/projects/{alpha['id']}", headers=auth_a), 200).json()
    assert project_after["my_finished_seconds"] == 90 + 30 + 15
    assert project_after["name"] == "Alpha v2"

    before_patch = must(client.get(f"/api/projects/{alpha['id']}/entries", headers=auth_a), 200).json()
    must(
        client.patch(
            f"/api/projects/{alpha['id']}/entries/{omitted['id']}",
            headers=auth_a,
            json={"duration_seconds": 1, "note": "changed", "work_date": "2000-01-01"},
        ),
        405,
    )
    must(
        client.put(
            f"/api/projects/{alpha['id']}/entries/{omitted['id']}",
            headers=auth_a,
            json={"duration_seconds": 1, "note": "changed", "work_date": "2000-01-01"},
        ),
        405,
    )
    after_patch = must(client.get(f"/api/projects/{alpha['id']}/entries", headers=auth_a), 200).json()
    assert before_patch == after_patch
    stored = entry_row(omitted["id"])
    assert stored is not None
    assert stored.duration_seconds == 90
    assert stored.note == "alpha-private"
    assert stored.work_date.isoformat() == "2026-10-07"

    must(client.delete(f"/api/projects/{alpha['id']}/entries/{teammate['id']}", headers=auth_a), 404)
    theirs = must(client.get(f"/api/projects/{alpha['id']}/entries", headers=auth_b), 200).json()
    assert any(row["id"] == teammate["id"] and row["duration_seconds"] == 50 for row in theirs)

    must(client.delete(f"/api/projects/{alpha['id']}/entries/{explicit_null['id']}", headers=auth_a), 204)
    after_own_delete = must(client.get(f"/api/projects/{alpha['id']}/entries", headers=auth_a), 200).json()
    assert explicit_null["id"] not in {row["id"] for row in after_own_delete}
    dropped = must(client.get(f"/api/projects/{alpha['id']}", headers=auth_a), 200).json()
    assert dropped["my_finished_seconds"] == 90 + 15

    # Wrong team does not create rows.
    before_secret = project_rows(secret["id"])
    must(
        client.post(f"/api/projects/{secret['id']}/entries", headers=auth_a, json={"duration_seconds": 10}),
        404,
    )
    must(client.get(f"/api/projects/{secret['id']}/entries", headers=auth_a), 404)
    assert project_rows(secret["id"]) == before_secret

    # Timer: start, same session on a later read, manual overlap does not touch it.
    started = must(client.post(f"/api/projects/{alpha['id']}/timer/start", headers=auth_a), 200).json()
    assert set(started.keys()) == SESSION_KEYS
    assert started["status"] == "running"
    assert started["project_id"] == alpha["id"]
    assert started["accumulated_seconds"] == 0
    assert started["segment_started_at"] is not None
    timer_row = entry_row(started["id"])
    assert timer_row is not None
    assert timer_row.user_id == user_a_id
    assert timer_row.project_id == alpha["id"]
    assert timer_row.source == "timer"
    assert timer_row.segment_started_at is not None
    assert timer_row.ended_at is None
    assert timer_row.duration_seconds == 0

    clock.advance(30)
    reread = must(client.get(f"/api/projects/{alpha['id']}/timer", headers=auth_a), 200).json()
    assert reread["id"] == started["id"]
    assert reread["segment_started_at"] == started["segment_started_at"]
    assert reread["accumulated_seconds"] == 0
    assert reread["status"] == "running"
    assert reread["server_now"] != started["server_now"]
    running_view = must(client.get(f"/api/projects/{alpha['id']}", headers=auth_a), 200).json()
    assert running_view["my_finished_seconds"] == 90 + 15
    assert running_view["my_session"]["id"] == started["id"]
    assert running_view["my_session"]["status"] == "running"

    overlap = must(
        client.post(
            f"/api/projects/{alpha['id']}/entries",
            headers=auth_a,
            json={"duration_seconds": 45, "note": "overlaps-timer"},
        ),
        201,
    ).json()
    assert overlap["source"] == "manual"
    still = must(client.get(f"/api/projects/{alpha['id']}/timer", headers=auth_a), 200).json()
    assert still["id"] == started["id"]
    assert still["segment_started_at"] == started["segment_started_at"]
    assert still["status"] == "running"
    assert any(row.source == "manual" and row.id == overlap["id"] for row in project_rows(alpha["id"]))
    assert must(client.get(f"/api/projects/{alpha['id']}", headers=auth_a), 200).json()["my_finished_seconds"] == 90 + 15 + 45

    # Open sessions are not deleted.
    must(client.delete(f"/api/projects/{alpha['id']}/entries/{started['id']}", headers=auth_a), 404)
    assert entry_row(started["id"]) is not None
    assert must(client.get(f"/api/projects/{alpha['id']}/timer", headers=auth_a), 200).json()["id"] == started["id"]

    clock.advance(125)
    paused = must(client.post(f"/api/projects/{alpha['id']}/timer/pause", headers=auth_a), 200).json()
    assert paused["id"] == started["id"]
    assert paused["status"] == "paused"
    assert paused["segment_started_at"] is None
    # 30s unread gap plus 125s. The unread gap is still part of the open segment.
    assert paused["accumulated_seconds"] == 155
    assert must(client.get(f"/api/projects/{alpha['id']}", headers=auth_a), 200).json()["my_finished_seconds"] == 90 + 15 + 45

    already = must(client.post(f"/api/projects/{alpha['id']}/timer/pause", headers=auth_a), 200).json()
    assert already["accumulated_seconds"] == 155
    assert already["status"] == "paused"

    clock.advance(1000)
    resumed = must(client.post(f"/api/projects/{alpha['id']}/timer/start", headers=auth_a), 200).json()
    assert resumed["id"] == started["id"]
    assert resumed["status"] == "running"
    assert resumed["accumulated_seconds"] == 155
    assert resumed["segment_started_at"] is not None
    assert resumed["segment_started_at"] != started["segment_started_at"]

    clock.advance(10.9)
    paused_again = must(client.post(f"/api/projects/{alpha['id']}/timer/pause", headers=auth_a), 200).json()
    assert paused_again["accumulated_seconds"] == 165
    assert paused_again["segment_started_at"] is None

    clock.advance(80)
    filed_paused = must(client.post(f"/api/projects/{alpha['id']}/timer/stop", headers=auth_a), 200).json()
    assert set(filed_paused.keys()) == ENTRY_KEYS
    assert filed_paused["source"] == "timer"
    assert filed_paused["duration_seconds"] == 165
    assert filed_paused["work_date"] == clock.now.date().isoformat()
    assert must(client.get(f"/api/projects/{alpha['id']}/timer", headers=auth_a), 404)
    assert must(client.get(f"/api/projects/{alpha['id']}", headers=auth_a), 200).json()["my_finished_seconds"] == 90 + 15 + 45 + 165

    # Running time is outside the finished total until stop.
    fresh = must(client.post("/api/projects", headers=auth_a, json={"name": "Timer only"}), 201).json()
    run = must(client.post(f"/api/projects/{fresh['id']}/timer/start", headers=auth_a), 200).json()
    clock.advance(40)
    assert must(client.get(f"/api/projects/{fresh['id']}", headers=auth_a), 200).json()["my_finished_seconds"] == 0
    stopped = must(client.post(f"/api/projects/{fresh['id']}/timer/stop", headers=auth_a), 200).json()
    assert stopped["source"] == "timer"
    assert stopped["duration_seconds"] == 40
    assert must(client.get(f"/api/projects/{fresh['id']}", headers=auth_a), 200).json()["my_finished_seconds"] == 40

    # Start B while A is running: pause A, do not stop it. Only B runs.
    project_a = must(client.post("/api/projects", headers=auth_a, json={"name": "Job A"}), 201).json()
    project_b = must(client.post("/api/projects", headers=auth_a, json={"name": "Job B"}), 201).json()
    first = must(client.post(f"/api/projects/{project_a['id']}/timer/start", headers=auth_a), 200).json()
    clock.advance(7)
    second = must(client.post(f"/api/projects/{project_b['id']}/timer/start", headers=auth_a), 200).json()
    paused_a = must(client.get(f"/api/projects/{project_a['id']}/timer", headers=auth_a), 200).json()
    assert paused_a["id"] == first["id"]
    assert paused_a["status"] == "paused"
    assert paused_a["segment_started_at"] is None
    assert paused_a["accumulated_seconds"] == 7
    assert second["status"] == "running"
    assert second["id"] != first["id"]
    assert running_ids(user_a_id) == [second["id"]]
    paused_row = entry_row(first["id"])
    assert paused_row is not None and paused_row.ended_at is None

    again = must(client.post(f"/api/projects/{project_b['id']}/timer/start", headers=auth_a), 200).json()
    assert again["id"] == second["id"]
    assert again["segment_started_at"] == second["segment_started_at"]
    assert running_ids(user_a_id) == [second["id"]]

    # A second running insert is rejected by the partial unique index.
    session = SessionFactory()
    try:
        extra = TimeEntry(
            user_id=user_a_id,
            project_id=project_a["id"],
            source="timer",
            work_date=None,
            duration_seconds=0,
            segment_started_at=clock.now,
            ended_at=None,
        )
        session.add(extra)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("two running timers were stored")
    finally:
        session.close()
    assert running_ids(user_a_id) == [second["id"]]

    # Teammate cannot read or stop my session.
    must(client.get(f"/api/projects/{project_b['id']}/timer", headers=auth_b), 404)
    must(client.post(f"/api/projects/{project_b['id']}/timer/stop", headers=auth_b), 404)
    must(client.post(f"/api/projects/{project_b['id']}/timer/pause", headers=auth_b), 404)
    mine_still = must(client.get(f"/api/projects/{project_b['id']}/timer", headers=auth_a), 200).json()
    assert mine_still["id"] == second["id"]
    assert mine_still["status"] == "running"
    assert mine_still["segment_started_at"] == second["segment_started_at"]

    # One running timer across teams: starting on team B pauses the team A timer.
    cross = must(client.post("/api/projects", headers=auth_a_b, json={"name": "Cross"}), 201).json()
    clock.advance(4)
    cross_session = must(client.post(f"/api/projects/{cross['id']}/timer/start", headers=auth_a_b), 200).json()
    assert cross_session["status"] == "running"
    paused_b = must(client.get(f"/api/projects/{project_b['id']}/timer", headers=auth_a), 200).json()
    assert paused_b["status"] == "paused"
    assert paused_b["id"] == second["id"]
    assert entry_row(second["id"]).ended_at is None  # type: ignore[union-attr]
    assert running_ids(user_a_id) == [cross_session["id"]]

    # Still running after midnight. Elapsed includes the overnight gap; it is not filed.
    overnight_start = _parse_utc(cross_session["segment_started_at"])
    session = SessionFactory()
    try:
        row = session.get(TimeEntry, cross_session["id"])
        assert row is not None
        row.segment_started_at = overnight_start - timedelta(hours=30)
        session.commit()
        stored_start = row.segment_started_at
    finally:
        session.close()
    later = must(client.get(f"/api/projects/{cross['id']}/timer", headers=auth_a_b), 200).json()
    assert later["id"] == cross_session["id"]
    assert later["status"] == "running"
    assert later["accumulated_seconds"] == 0
    parsed_start = _parse_utc(later["segment_started_at"])
    parsed_now = _parse_utc(later["server_now"])
    assert parsed_now - parsed_start >= timedelta(hours=25)
    assert must(client.get(f"/api/projects/{cross['id']}", headers=auth_a_b), 200).json()["my_finished_seconds"] == 0
    assert stored_start is not None

    # User B still has no session of their own on this project.
    must(client.get(f"/api/projects/{alpha['id']}/timer", headers=auth_b), 404)
    assert user_b_id != user_a_id
    assert alpha_again["name"] == "Alpha"
    assert long_name["name"] == "N" * 255


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


if __name__ == "__main__":
    main()
