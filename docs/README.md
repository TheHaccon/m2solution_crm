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
| Accounting (annual report) | [features/accounting.md](features/accounting.md) |
| Expenses | [features/expenses.md](features/expenses.md) |
| Public invoice links and view counts | [features/public-invoice-links.md](features/public-invoice-links.md) |
| Meeting notes | [features/meetings.md](features/meetings.md) |
| Markdown notes | [features/markdown.md](features/markdown.md) |
| Teams | [features/teams.md](features/teams.md) |
| Project time tracking | [features/project-time-tracking.md](features/project-time-tracking.md) |
| Dark mode | [features/dark-mode.md](features/dark-mode.md) |
| File manager | [features/file-manager.md](features/file-manager.md) |
| Staff dashboard | [features/dashboard.md](features/dashboard.md) |
| Docker | [features/docker.md](features/docker.md) |
| Postgres | [features/postgres.md](features/postgres.md) |
| Shared Postgres (host cluster) | [features/shared-postgres.md](features/shared-postgres.md) |
| Postgres replica / failover | [features/backups.md](features/backups.md) |

## Also read

- [overview.md](overview.md) — product scope and what v1 does not include
- [architecture.md](architecture.md) — stack, folders, data model, env
- [run.md](run.md) — local and Docker
- [delivery/16-invoice-schema-drift.md](delivery/16-invoice-schema-drift.md) — delivery report for invoice/client schema repair (#16)
- [delivery/feature-project-time-tracking.md](delivery/feature-project-time-tracking.md) — delivery report for team projects and personal timers (#19–#22)
- [delivery/24-timer-stop-note.md](delivery/24-timer-stop-note.md) — optional note when staff stop a timer (#24)

