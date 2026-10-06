# Delivery: Project time tracking

## Status
pr-open

## Links
- Issue(s): #19 — https://github.com/TheHaccon/m2solution_crm/issues/19 · #20 — https://github.com/TheHaccon/m2solution_crm/issues/20 · #21 — https://github.com/TheHaccon/m2solution_crm/issues/21 · #22 — https://github.com/TheHaccon/m2solution_crm/issues/22
- Input doc: docs/input/2026-10-06-project-time-tracking.md
- Branch: `feature/project-time-tracking`
- PR: https://github.com/TheHaccon/m2solution_crm/pull/23

## Summary
Staff on the active team can create and rename named projects, then log only their own hours. A server-side timer (start, pause, stop) survives reload. Manual add records a finished duration without starting the timer. There is no project delete, no client link, and no team total.

## Changes
### UI
- Sidebar **Projects** (`StaffLayout.tsx`), with Clients and Meetings.
- `/projects` — create by name, rename in the row, personal finished total and live session (`ProjectsListPage.tsx`).
- `/projects/:id` — Start, Pause, and Stop as three buttons; Add time (date defaults to server today, hours/minutes/seconds, optional note); delete own finished rows (`ProjectDetailPage.tsx`, `SessionElapsed.tsx`).
- Signed-out `/projects` lands on login. No client field, archive, project delete, team total, or in-place edit.

### API / backend
- Staff JWT and `X-Team-Id` on every `/api/projects` route (`backend/app/api/projects.py`).
- Projects: `GET/POST /api/projects`, `GET/PATCH /api/projects/{id}`. Name only. Blank name rejected. Duplicate names allowed. No delete. Other team is 404. Missing team header 400, missing token 401, non-member 403.
- Entries: `GET/POST /api/projects/{id}/entries`, `DELETE /api/projects/{id}/entries/{entry_id}`. Own finished rows only. Manual date defaults to server UTC today. `duration_seconds` must be a positive integer. Optional note. No in-place edit (`PATCH` and `PUT` 405).
- Timer: `GET /api/projects/{id}/timer`, `POST .../timer/start|pause|stop`. One running timer per user. Starting another project pauses the current one. Running time joins the finished total only on Stop. Server clock wins.

### Data / config / migrations
- Tables `projects` and `time_entries` (`backend/app/models/project.py`).
- Alembic `006_projects` (`backend/alembic/versions/006_projects.py`), partial unique index `uq_time_entries_one_running`.

### Evergreen docs
- `docs/features/project-time-tracking.md`
- `docs/README.md` feature table and delivery link
- `docs/architecture.md` data model, Alembic `006_projects`, and the project/time auth bullet

## Testing
### Automated
- Commands: `backend/.venv/bin/python backend/scripts_test_project_time.py` (from `/srv/m2solution_crm`); `npx tsc -p tsconfig.app.json --noEmit` (from `frontend`)
- Result: pass
- The script covers #19–#21 on an in-memory database: team header 400, non-member 403, missing token 401, other-team 404, blank name rejected, duplicate names allowed, no project delete, personal entries, no in-place edit (PATCH and PUT 405), overlaps, one running timer, pause/resume without double-count, stop files a timer entry, running time excluded from the finished total, no midnight auto-stop, teammate cannot read or stop the session.

### Manual
- Steps: Dev stack crm-dev already up (127.0.0.1:5173 / 127.0.0.1:8000, database crm_dev). Signed-out /projects landed on login. Seed password does not authenticate existing crm_dev users, so the click-through used a temporary staff user on two new teams, then that user, both teams, 3 projects, and 4 entries were deleted. Playwright Chromium on this host: sidebar Projects with Clients and Meetings; create and rename; no client field, archive, project delete, team total, or in-place edit. Start, Pause, and Stop are three labeled buttons. Reload kept the running timer. Pause held accumulated time and did not file it. Resume stayed one session. Stop added a timer row to the finished total. Manual add (default date 2026-10-06, 1 minute, note) did not start a timer; deleting that row dropped the minute and left the timer row. Starting a second project paused the first and left its finished total unchanged. The other team’s list did not show the project. Live elapsed moved from 0:00:00 to 0:00:02 while Finished stayed at the filed total; Stop then increased Finished.
- Result: pass

### Tester sign-off
Approved for documenter: staff project list, rename, personal timer (start, pause, stop), manual add, and delete-own were verified against issues #19–#22 on feature/project-time-tracking.

### Not verified
- Cursor’s browser tab is a different machine: http://127.0.0.1:5173 there is NaturART, not this CRM. The flow was Playwright Chromium on the server.
- A real overnight wait. The API script backdates the start instead.
- A second real staff account in the UI. Teammate hiding is covered by the API script.
- Signing in as the existing seed user. Passwords were not changed.

## Screenshots / recordings
- **N/A** (Playwright on the host, no recording saved).

## Risks / follow-ups
- Stopping a timer in the same second can file `duration_seconds` 0. A manual entry of 0 is 422. A backward server clock adds 0 seconds for that segment instead of a negative amount.
- `docs/features` page was missing at test time; this delivery adds `docs/features/project-time-tracking.md`.
- `SEED_PASSWORD` `changeme` is rejected for existing crm_dev users (`admin@m2solution.com` and the two Gmail seed addresses). Pre-existing, out of this feature. Passwords were not reset.

## GitHub — commit (for Orchestrator or explicit user request)
### Subject
Document team projects and personal timers for the staff hours batch.

### Body
Explain project and time-entry behavior, routes, and the new tables so reviewers can check #19–#22 without reading only the diff.

## GitHub — pull request
### Title
Add team projects and a personal server-side timer (#19–#22)

### Body
## Summary
- Staff share team project names (create and rename only) and log their own hours.
- Server-side timer: start, pause, stop. One running timer per user. Running time joins the finished total only on Stop.
- Manual add (server UTC today by default, integer seconds, optional note) and delete-own. No in-place edit, no project delete, no client link.

## Test plan
- [x] `backend/.venv/bin/python backend/scripts_test_project_time.py` (in-memory, #19–#21)
- [x] `npx tsc -p tsconfig.app.json --noEmit` in `frontend`
- [x] Playwright on the dev host: sidebar Projects, create/rename, start/pause/stop, manual add, delete-own, second project pauses the first, other team does not list it
- [ ] Reviewer: confirm Alembic `006_projects` on the target database (`alembic upgrade head`)

## Linked issues
Closes #19
Closes #20
Closes #21
Closes #22
