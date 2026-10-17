"""Wipe and repopulate crm_dev with demo data. Never run against production crm."""
from __future__ import annotations

import argparse
import sys

from app.core.config import settings
from app.core.database import SessionLocal
from app.seeds.context import DEV_PUBLIC_INVOICE_TOKEN, DevSeedContext
from app.seeds.registry import run_dev_seeds
from app.seeds.wipe import assert_dev_database, database_name_from_url, wipe_database_tables, wipe_files_root
from app.services.invoices import share_url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reset crm_dev database and dev file blobs, then seed demo data.")
    parser.add_argument(
        "--no-files",
        action="store_true",
        help="Skip wiping FILES_ROOT (database still truncated).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only verify DATABASE_URL is crm_dev; make no changes.",
    )
    args = parser.parse_args(argv)

    assert_dev_database()
    db_name = database_name_from_url(settings.database_url)
    print(f"Target database: {db_name}")

    if args.dry_run:
        print("Dry run OK — no changes made.")
        return 0

    print("Truncating application tables…")
    wipe_database_tables()
    print("Clearing file blobs…")
    wipe_files_root(skip=args.no_files)

    ctx = DevSeedContext(settings=settings)
    db = SessionLocal()
    try:
        run_dev_seeds(db, ctx)
        db.commit()
        primary = ctx.primary_user.email if ctx.primary_user else "(none)"
        client_count = len(ctx.clients)
        project_count = len(ctx.projects)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print("Dev reseed complete.")
    print(f"  Login: {primary} / (SEED_PASSWORD from env, default changeme)")
    print(f"  Team: M2 Solution — clients {client_count}, projects {project_count}")
    token = DEV_PUBLIC_INVOICE_TOKEN
    print(f"  Public sent invoice: {share_url(token)}")
    print(f"  Token: {token}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
