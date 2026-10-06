# Scratch: Project tab with a timer

## Status
promoted

## Linked input
docs/input/2026-10-06-project-time-tracking.md

## Session notes (append newest at bottom)

### 2026-10-06 12:40 — turn summary
- **User:** Can we add a Projet tab with a timer you can start, pause, add, and stop, so we can count time spent on each project?
- **Agent:** Feasible. Sidebar today is Dashboard, Clients, Invoices, Expenses, Accounting, Meetings, Files. No project entity and no time log. Clients are billing contacts, not work projects. “Add” is ambiguous (new project vs manual time entry). Live timer must be stored on the server or closing the tab loses the clock.
- **Open threads:** Is a project a client job, an internal named bucket, or both? Does “add” mean a manual duration, or creating a project? One running timer, or many? Team-shared or personal? Bill hours onto invoices later, or log only?

### 2026-10-06 12:43 — turn summary
- **User:** Log only for now. Projects do not need a client. “Add” means both creating a project and a manual time entry. Each person has their own hours.
- **Agent:** Direction is a personal time log on named projects, no invoice link. Still open: is the project list shared by the team (same project, separate hours) or does each person keep a private project list? One running timer at a time is the safer default.
- **Open threads:** Shared project names vs private projects. One active timer. Lock the write-up?

### 2026-10-06 12:44 — turn summary
- **User:** A — team shares the project list; each person sees only their own hours.
- **Agent:** Promoted to `docs/input/2026-10-06-project-time-tracking.md` (status draft). Assumed: any teammate can create and rename; no project delete; owner can delete their own entries; one running timer per user; manual entry is date + duration + optional note; no in-place edit. Asking gate 1.
- **Open threads:** Gate 1 — create GitHub issues from the draft?

## Raw bullets
- Staff sidebar links live in `frontend/src/layouts/StaffLayout.tsx`. A new “Projects” item would be another route, same pattern as Meetings or Expenses.
- Clients are team-scoped. Invoices belong to the staff member who created them. Expenses are personal. Time tracking has to pick one of those ownership models.
- Controls named: start, pause, add, stop.
- Goal: count time passed on each project (“our” time — maybe the team, maybe each person).
- Locked so far: log only (no invoice lines). Project is a name, not a client. Create project + manual duration. Hours belong to the person who logged them. Server stores the running start time.

## Risks / dumb ideas / maybes
- Browser-only timer dies on refresh and cannot be trusted as the source of hours.
- Two people starting timers on the same project at once — shared clock vs each person’s sessions.
- Invoice lines are explicitly later. Do not build billing in this slice.
- If projects are private, two people both name a project “Website” and never see each other’s list. If projects are shared, they share the name and each still sees only their own hours.
- “Add” might mean “I forgot to start the timer; enter 1h 30m by hand.”
- Pause vs stop: pause keeps the session open; stop closes it and adds the duration to the project total.
