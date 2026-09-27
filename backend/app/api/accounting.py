import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.accounting import AccountingOut
from app.services.accounting import build_accounting

router = APIRouter(prefix="/api/accounting", tags=["accounting"])


def _year_param(year: int | None) -> int:
    value = year if year is not None else date.today().year
    if value < 2000 or value > 2100:
        raise HTTPException(status_code=400, detail="year must be between 2000 and 2100")
    return value


@router.get("", response_model=AccountingOut)
def get_accounting(
    year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AccountingOut:
    report = build_accounting(db, user, _year_param(year))
    db.commit()
    return report


@router.get("/export")
def export_accounting(
    year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    report = build_accounting(db, user, _year_param(year))
    db.commit()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["number", "client", "issue_date", "paid_at", "status", "total"])
    for row in report.invoices:
        paid = row.paid_at.date().isoformat() if row.paid_at else ""
        writer.writerow([row.number, row.client_name, row.issue_date.isoformat(), paid, row.status, f"{row.total:.2f}"])
    writer.writerow([])
    writer.writerow(["date", "category", "vendor", "amount"])
    for row in report.expenses:
        writer.writerow(
            [row.spent_on.isoformat(), row.category_name, row.vendor or "", f"{row.amount:.2f}"]
        )
    filename = f"accounting-{report.year}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
