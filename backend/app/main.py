from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.accounting import router as accounting_router
from app.api.auth import router as auth_router
from app.api.clients import router as clients_router
from app.api.dashboard import router as dashboard_router
from app.api.expenses import router as expenses_router
from app.api.files import router as files_router
from app.api.invoices import router as invoices_router
from app.api.meetings import router as meetings_router
from app.api.projects import router as projects_router
from app.api.public import router as public_router
from app.api.teams import router as teams_router
from app.core.config import seed_display_name, settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import Client, Expense, ExpenseCategory, ExpenseRecurrence, FileNode, Invoice, InvoiceLineItem, InvoiceView, Meeting, Project, Team, TeamMember, TimeEntry, User  # noqa: F401

DEFAULT_TEAM_NAME = "M2 Solution"


def seed_staff() -> None:
    db = SessionLocal()
    try:
        team = db.scalar(select(Team).where(Team.name == DEFAULT_TEAM_NAME).order_by(Team.id))
        if team is None:
            team = Team(name=DEFAULT_TEAM_NAME)
            db.add(team)
            db.flush()
        for email in settings.seed_email_list:
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(
                    email=email,
                    password_hash=hash_password(settings.seed_password),
                    full_name=seed_display_name(email),
                )
                db.add(user)
                db.flush()
            membership = db.scalar(
                select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.user_id == user.id)
            )
            if membership is None:
                db.add(TeamMember(team_id=team.id, user_id=user.id))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_staff()
    yield


app = FastAPI(title="M2 Solution CRM", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(teams_router)
app.include_router(clients_router)
app.include_router(invoices_router)
app.include_router(meetings_router)
app.include_router(projects_router)
app.include_router(dashboard_router)
app.include_router(files_router)
app.include_router(expenses_router)
app.include_router(accounting_router)
app.include_router(public_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
