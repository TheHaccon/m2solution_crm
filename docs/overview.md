# Overview

M2 Solution CRM is an internal tool to manage **clients**, **invoices**, and **meeting documentation**.

## Who uses it

- **Staff** sign in with email/password and run the CRM (clients, invoices, meetings, dashboard).
- **Clients** never create an account. Staff send a secret invoice URL; anyone with that link can view (and print) that one invoice.

## v1 behavior

- Create draft invoices with line items, then **Send** to generate a share link.
- Staff **mark paid** by hand. There is **no** payment processor (no Stripe, PayPal, etc.).
- Opening the public link increments a **view count** (rapid refreshes from the same browser are ignored).
- Meeting notes are **staff-only** and never appear on the public invoice.

## Out of scope (v1)

- Client login / client portal
- Emailing invoices from the app (copy the link yourself)
- Estimates, recurring invoices, tax, multi-currency, inventory
- File attachments
- Multi-company / multi-tenant
