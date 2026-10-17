from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from app.core.config import settings
from app.core.database import Base, engine
from app.models import Client, Expense, ExpenseCategory, ExpenseRecurrence, FileNode, Invoice, InvoiceLineItem, InvoiceView, Meeting, Project, Team, TeamMember, TimeEntry, User  # noqa: F401
from app.seeds.staff import seed_staff


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
