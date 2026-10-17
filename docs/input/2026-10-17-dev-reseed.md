# Dev reseed and seed-data discipline

Status: ready-for-github

## Summary

Staff need a safe way to wipe and repopulate **crm_dev** with demo data covering every CRM feature, plus a rule that new features ship dev seed examples. Remove the obsolete `admin@m2solution.com` password-reset gate; all staff are admins in this personal CRM.

## User story

As a developer on the dev stack, I want one command to reset `crm_dev` and file blobs to a known demo state so I can explore the app and test features without manual SQL or stale passwords.

## Acceptance criteria

### Dev reseed CLI

- **Given** `DATABASE_URL` points at database `crm_dev`
- **When** I run the documented reseed command
- **Then** app tables are truncated (except `alembic_version`), dev `FILES_ROOT` is cleared, seed staff passwords match `SEED_PASSWORD`, and demo rows exist for clients, meetings, invoices (all statuses), expenses, files, projects/time, and accounting-relevant dates

### Safety

- **Given** `DATABASE_URL` points at `crm` (prod)
- **When** I run reseed without override
- **Then** the command exits with an error and makes no changes

### Auth cleanup

- **Given** any signed-in staff user
- **When** they use Reset staff password
- **Then** the API allows it (no `admin@m2solution.com` check)

### Discipline

- **Given** a new user-facing feature PR
- **When** merged
- **Then** dev seeds and `docs/features/dev-seeding.md` are updated (Cursor rule)

## Out of scope

- Reseeding production `crm`
- Email password reset / invites
- Rewriting archived delivery/brainstorm docs

## Notes

- Feature batch: `dev-reseed`
- Stable public invoice token for docs: `dev-demo-invoice-public-token`
