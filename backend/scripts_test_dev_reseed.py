"""Verify dev reseed against crm_dev (skips when DATABASE_URL is not crm_dev)."""
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.project import Project
from app.seeds.context import DEV_PUBLIC_INVOICE_TOKEN
from app.seeds.cli import main as reseed_main
from app.seeds.wipe import ALLOWED_DEV_DATABASE, database_name_from_url


def main() -> None:
    db_name = database_name_from_url(settings.database_url)
    if db_name != ALLOWED_DEV_DATABASE:
        print(f"skip dev reseed test (database is {db_name!r}, not {ALLOWED_DEV_DATABASE!r})")
        return

    assert reseed_main([]) == 0

    db = SessionLocal()
    try:
        client_count = db.scalar(select(func.count()).select_from(Client)) or 0
        assert client_count >= 1, client_count
        project_count = db.scalar(select(func.count()).select_from(Project)) or 0
        assert project_count >= 1, project_count
        sent = db.scalar(select(Invoice).where(Invoice.public_token == DEV_PUBLIC_INVOICE_TOKEN))
        assert sent is not None, "expected sent invoice with dev public token"
        assert sent.status == "sent", sent.status
    finally:
        db.close()

    print("dev reseed checks passed")


if __name__ == "__main__":
    main()
