"""Smoke-test auth, clients, invoices, public views, meetings."""
from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    with TestClient(app) as client:
        login = client.post("/api/auth/login", json={"email": "admin@m2solution.com", "password": "changeme"})
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/api/auth/me", headers=headers)
        assert me.status_code == 200, me.text

        created = client.post(
            "/api/clients",
            headers=headers,
            json={"name": "Acme Co", "email": "acme@example.com", "phone": "555-0100", "address": "1 Main St", "notes": "VIP"},
        )
        assert created.status_code == 201, created.text
        client_id = created.json()["id"]

        inv = client.post(
            "/api/invoices",
            headers=headers,
            json={
                "client_id": client_id,
                "issue_date": date.today().isoformat(),
                "due_date": date.today().isoformat(),
                "notes": "Net 15",
                "line_items": [{"description": "Consulting", "quantity": 2, "unit_price": "150.00"}],
            },
        )
        assert inv.status_code == 201, inv.text
        invoice_id = inv.json()["id"]
        assert float(inv.json()["total"]) == 300

        public = client.get(f"/api/public/invoices/{inv.json().get('public_token') or 'missing'}")
        assert public.status_code == 404

        sent = client.post(f"/api/invoices/{invoice_id}/send", headers=headers)
        assert sent.status_code == 200, sent.text
        token_pub = sent.json()["public_token"]
        assert token_pub

        v1 = client.get(f"/api/public/invoices/{token_pub}", headers={"X-Viewer-Id": "viewer-a"})
        assert v1.status_code == 200, v1.text
        v2 = client.get(f"/api/public/invoices/{token_pub}", headers={"X-Viewer-Id": "viewer-a"})
        assert v2.status_code == 200
        staff = client.get(f"/api/invoices/{invoice_id}", headers=headers)
        assert staff.json()["view_count"] == 1, staff.json()

        v3 = client.get(f"/api/public/invoices/{token_pub}", headers={"X-Viewer-Id": "viewer-b"})
        assert v3.status_code == 200
        staff = client.get(f"/api/invoices/{invoice_id}", headers=headers)
        assert staff.json()["view_count"] == 2, staff.json()

        paid = client.post(f"/api/invoices/{invoice_id}/mark-paid", headers=headers)
        assert paid.status_code == 200
        assert paid.json()["status"] == "paid"

        meeting = client.post(
            "/api/meetings",
            headers=headers,
            json={
                "client_id": client_id,
                "title": "Kickoff",
                "scheduled_at": datetime.now(timezone.utc).isoformat(),
                "attendees": "Alex, Sam",
                "body": "# Notes\n- Scope agreed",
            },
        )
        assert meeting.status_code == 201, meeting.text

        dash = client.get("/api/dashboard", headers=headers)
        assert dash.status_code == 200, dash.text
        print("ok", dash.json()["paid_count"], "paid,", "views" if dash.json()["recent_views"] else "no views")


if __name__ == "__main__":
    main()
