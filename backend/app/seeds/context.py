from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.core.config import Settings
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.project import Project
from app.models.team import Team
from app.models.user import User

DEV_PUBLIC_INVOICE_TOKEN = "dev-demo-invoice-public-token"
SECOND_TEAM_NAME = "Demo Client Co"


@dataclass
class DevSeedContext:
    settings: Settings
    primary_user: User | None = None
    secondary_user: User | None = None
    main_team: Team | None = None
    second_team: Team | None = None
    clients: list[Client] = field(default_factory=list)
    invoices: dict[str, Invoice] = field(default_factory=dict)
    projects: list[Project] = field(default_factory=list)
    seed_year: int = field(default_factory=lambda: date.today().year)
