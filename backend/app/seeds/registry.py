from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from app.seeds.context import DevSeedContext
from app.seeds.demo_clients import seed_demo_clients
from app.seeds.demo_expenses import seed_demo_expenses
from app.seeds.demo_files import seed_demo_files
from app.seeds.demo_invoices import seed_demo_invoices
from app.seeds.demo_meetings import seed_demo_meetings
from app.seeds.demo_projects import seed_demo_projects
from app.seeds.staff import seed_staff_dev

SeedFn = Callable[[Session, DevSeedContext], None]

DEV_SEED_REGISTRY: list[SeedFn] = [
    seed_staff_dev,
    seed_demo_clients,
    seed_demo_meetings,
    seed_demo_invoices,
    seed_demo_expenses,
    seed_demo_files,
    seed_demo_projects,
]


def run_dev_seeds(db: Session, ctx: DevSeedContext) -> None:
    for fn in DEV_SEED_REGISTRY:
        fn(db, ctx)
