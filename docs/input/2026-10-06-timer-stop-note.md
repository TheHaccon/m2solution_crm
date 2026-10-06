# Prompt for a note when stopping the timer

## Status
ready-for-github

## Change type
feature

## Summary
On a project page, **Stop** asks for an optional note before the session is filed. Confirming stop saves that note on the finished entry. Dismissing the prompt leaves the timer running.

## Motivation
**Add time** already takes an optional note. **Stop** files the session with no note, and a finished entry cannot be edited afterward. Staff who time a job have no place to say what they did unless they delete the row and type the duration by hand.

## Detailed intent
- **Stop** on `/projects/:id` opens a prompt with a note field and the elapsed time about to be filed.
- The note is optional. A blank note stops the same way as today (`note` null).
- **Confirm** calls `POST /api/projects/{id}/timer/stop` with that note and then shows the finished row, note included.
- **Cancel** (or dismiss) does not call stop. The session stays running or paused, exactly as it was.
- Pause does not prompt. Start does not prompt.
- The note is stored on the existing `time_entries.note` column. No new table.
- Finished entries still cannot be edited. The only chance to write the note is this prompt.

## Constraints
- Staff only, same project page as the timer.
- One running timer per user is unchanged.
- Empty or whitespace-only note is stored as null, same rule as manual **Add time**.
- This does not add edit, required notes, or a note on pause.

## Open questions
- None for this slice. User said "create" on 2026-10-06: a new issue, not a change to open pull request #23. That pull request stays open; its manifest is snapshotted under `docs/work/archive/` so this slice can take `active-slice.yaml`.

## Risks and criticism
- If stop is sent before the prompt, the note is lost: finished rows have no edit route (`PATCH` / `PUT` return 405). The prompt has to happen first, and the stop API has to accept the note. Today `stop_timer` always writes `note=None`.
- A modal that is easy to miss (or an accidental Enter) can file a session the user meant to keep open. Cancel must be the path that does nothing.
- A required note would block a quick stop. This slice keeps the note optional so stop stays one extra click, not a form they must fill.

## Out of scope
- Editing a note after the entry is filed.
- Prompting on pause, on switching projects, or on manual **Add time** (that form already has a note field).
- Making the note required.
- Team-visible notes or invoice text.

## Technical plan (draft)
- Extend stop so the request body may include `note` (optional string). Blank becomes null.
- Project detail: Stop opens the prompt; confirm posts the note; cancel closes the prompt.
- Tests: stop with a note persists it; stop with a blank note stores null; cancel does not file the session.

## Proposed issues (draft)
- One follow-up issue after #23 merges: prompt for an optional note on timer stop, and accept that note on the stop API.

## Raw notes
User, 2026-10-06: "when i press stop on the timer can it prompt me to add a note".
