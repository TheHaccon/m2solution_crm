# Overview

M2 Solution CRM is an internal tool to manage **clients**, **invoices**, and **meeting documentation**.

## Who uses it

- **Staff** sign in with email/password and run the CRM (clients, invoices, meetings, dashboard).
- **Clients** never create an account. Staff send a secret invoice URL; anyone with that link can view (and print) that one invoice.

## v1 behavior

- Create draft invoices with line items, then **Send** to generate a share link.
- Staff **mark paid** by hand. There is **no** payment processor (no Stripe, PayPal, etc.).
- **Accounting** shows a calendar-year billed / collected / outstanding report plus deductible **expenses**, net collected, a revenue-vs-expenses chart, and a category wheel (CSV export for the accountant).
- Staff record personal **expenses** (including monthly recurrences and receipts in Files).
- Opening the public link increments a **view count** (rapid refreshes from the same browser are ignored).
- Meeting notes are **staff-only** and never appear on the public invoice.
- Clients and meetings are scoped to the **active team**. Invoices belong to the staff member who created them.
- Staff store configs and uploads in **Files**: a team tree (shared) and a personal tree (private). Max 25 MB per file.

## Out of scope (v1)

- Client login / client portal
- Emailing invoices from the app (copy the link yourself)
- Estimates, recurring invoices, tax (TPS/TVQ), multi-currency, inventory, non-calendar fiscal year
- Google Drive sync (file manager is local disk only)
- Multi-company / separate tenants (teams share one company; they are not separate CRMs)
