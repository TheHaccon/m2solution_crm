from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.expense import Expense, ExpenseRecurrence
from app.seeds.context import DevSeedContext
from app.services.expenses import seed_categories


def seed_demo_expenses(db: Session, ctx: DevSeedContext) -> None:
    if ctx.primary_user is None:
        return
    user = ctx.primary_user
    categories = seed_categories(db, user)
    by_name = {c.name: c for c in categories}
    y = ctx.seed_year
    rows = [
        Expense(
            created_by_id=user.id,
            category_id=by_name["Gas"].id,
            amount=Decimal("62.40"),
            spent_on=date(y, 2, 8),
            vendor="Demo Gas Co",
            notes="Dev seed — accounting year",
        ),
        Expense(
            created_by_id=user.id,
            category_id=by_name["Subscription"].id,
            amount=Decimal("29.99"),
            spent_on=date(y, 7, 1),
            vendor="SaaS Example",
            notes="Monthly tool",
        ),
    ]
    for row in rows:
        db.add(row)
    db.flush()

    recurrence = ExpenseRecurrence(
        created_by_id=user.id,
        category_id=by_name["Auto"].id,
        amount=Decimal("45.00"),
        vendor="Parking pass",
        notes="Dev seed recurrence",
        day_of_month=1,
        start_on=date(y, 1, 1),
        next_on=date(y, 12, 1),
        active=True,
    )
    db.add(recurrence)
