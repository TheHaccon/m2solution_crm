from sqlalchemy.orm import Session

from app.models.client import Client
from app.seeds.context import DevSeedContext


def seed_demo_clients(db: Session, ctx: DevSeedContext) -> None:
    if ctx.main_team is None or ctx.primary_user is None:
        return
    specs = [
        {
            "name": "Acme Workshop",
            "email": "billing@acme-demo.example",
            "phone": "514-555-0100",
            "address": "100 Demo Street\nMontreal QC",
            "notes": "Dev seed client — invoices and meetings attached.",
        },
        {
            "name": "Northwind Labs",
            "email": "hello@northwind-demo.example",
            "phone": "514-555-0200",
            "address": "42 Sample Ave",
            "notes": "Second client for list filters.",
        },
        {
            "name": "Contoso Retail",
            "email": None,
            "phone": None,
            "address": None,
            "notes": "Minimal contact fields.",
        },
    ]
    ctx.clients = []
    for spec in specs:
        client = Client(team_id=ctx.main_team.id, **spec)
        db.add(client)
        db.flush()
        ctx.clients.append(client)
