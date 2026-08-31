# M2 Solution CRM docs

Internal CRM for billing and client meeting notes. Staff sign in. Clients do **not** — they open invoices from a secret link.

## How we document

**Every new feature gets a page in `docs/features/` in the same change as the code.** Copy [features/_TEMPLATE.md](features/_TEMPLATE.md), fill it in, and add a row to the table below.

## Features

| Feature | Doc |
| ------- | --- |
| Staff auth | [features/auth.md](features/auth.md) |
| Clients | [features/clients.md](features/clients.md) |
| Invoices | [features/invoices.md](features/invoices.md) |
| Public invoice links and view counts | [features/public-invoice-links.md](features/public-invoice-links.md) |
| Meeting notes | [features/meetings.md](features/meetings.md) |
| Staff dashboard | [features/dashboard.md](features/dashboard.md) |
| Docker | [features/docker.md](features/docker.md) |
| Postgres | [features/postgres.md](features/postgres.md) |
| Postgres replica / failover | [features/backups.md](features/backups.md) |

## Also read

- [overview.md](overview.md) — product scope and what v1 does not include
- [architecture.md](architecture.md) — stack, folders, data model, env
- [run.md](run.md) — local and Docker
