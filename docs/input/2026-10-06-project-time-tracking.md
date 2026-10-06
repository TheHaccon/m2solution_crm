# Team projects with a personal time log

## Status
ready-for-github

## Change type
feature

## Summary
Staff get a **Projects** page. The active team shares the project list. Each person logs their own time with a server-side timer (start, pause, stop) or by typing a finished duration. Totals show only that person’s hours. Nothing is linked to clients or invoices.

## Motivation
Staff need a place to count time spent on named jobs. The CRM has clients, invoices, and meetings, and no project or time log. Hours should survive a refresh or a closed tab, and two people on the same project should not overwrite each other’s time.

## Detailed intent
- Sidebar gains **Projects**, staff-only, same shell as Clients and Meetings.
- A project is a name on the **active team**. Any member of that team can create one and rename one. No client field.
- Everyone on the team sees the same project list, including projects they have not logged time on yet.
- Time belongs to the signed-in user. The list and the project page show **that user’s** total only. Teammates’ hours are not shown and cannot be edited.
- **Start** begins a session. The server stores who, which project, and when it started. The page can be closed; the clock keeps counting until pause or stop.
- **Pause** stops the clock and keeps the session open so **Start** continues it. **Stop** closes the session and adds its duration to the user’s total.
- Only one session runs per user. Starting or resuming a project pauses whichever other project session that user had running.
- **Add time** records a finished block: a date (default today), a duration, and an optional note. It does not start the live timer.
- The project page lists that user’s finished entries. The owner can delete their own entry. They cannot delete someone else’s.
- Projects are not deleted in this slice. Deleting a shared name would orphan or wipe other people’s hours.

## Constraints
- Log only. No invoice line, no rate, no billable flag, no client link.
- Team-scoped projects, same active-team header as clients (`X-Team-Id`). A project from another team is not visible.
- One running timer per user, not per browser tab.
- Staff only. No public page.

## Open questions
- None that change the direction. Edit of an existing entry (change duration or note) is not in this slice; delete and add again is enough. A later slice can add edit, archive, or billing.

## Risks and criticism
- A timer left running overnight (or over a weekend) becomes a huge entry on stop. The UI should show the live elapsed time clearly, including on the project list, so a forgotten clock is obvious. This slice does not auto-stop at midnight.
- Pause and stop are easy to confuse. Pause keeps the session; stop files it. The controls need those words, not a single toggle.
- Shared names with private hours means two people can both be “on Website” and never see that the other worked. That is intentional. A team total would be a different feature.
- Rename is shared. Renaming “Website” to “Website v2” changes the name for everyone. Their hours stay attached.
- Manual entry can overlap a live session or another block. This slice does not reject overlaps.
- Browser-only timing was rejected. If the server clock and the user’s laptop clock disagree, the server wins.

## Out of scope
- Linking a project to a client.
- Putting hours on an invoice or accounting report.
- Showing or exporting a teammate’s hours, or a combined team total.
- Deleting or archiving a project.
- Editing a finished entry in place.
- Rounding to 15 minutes, rates, or currency.
- More than one running timer per user.
- Reminders when a timer has been running a long time.

## Technical plan (draft)
- New team-scoped project row (name, team, timestamps).
- Time entry row: user, project, start, end, duration, optional note, source (`timer` or `manual`). A running session has a start and no end.
- Pause stores accumulated duration and clears the running start so resume does not double-count.
- API requires staff auth and `X-Team-Id`. Reads and writes of entries are limited to the current user.
- UI: list route plus project detail with timer controls and the manual form.

## Proposed issues (draft)
Left for GitHub decomposition after gate 1. Not split here.

## Raw notes
- Scratch: `docs/brain-storming/2026-10-06-project-time-tracking.md`
- User choices: log only; project not tied to a client; add means both create project and manual duration; each person sees their own hours; project list is shared by the team (option A).
