# Feature: Markdown notes

Date: 2026-09-01

## What it does

Staff meeting bodies and client internal notes render as markdown. Code written with backticks displays as code (no visible `` ` ``). The same component can be reused for later stored config text.

## Behavior

- Source is still plain text in the database. Forms are textareas; you see backticks while editing.
- On the meeting page and client notes card, markdown is rendered:
  - headings `#` `##` `###`
  - lists, bold, italic, strikethrough, quotes, links, GFM tables
  - `` `inline` `` → mono pill
  - fenced ` ``` ` blocks → navy `<pre>` (language tag ignored; no syntax colors)
- Meeting **list** snippets stay plain truncated text.
- Raw HTML in notes is not executed (`react-markdown`).

## API

None. Existing `meetings.body` and `clients.notes` fields.

## UI

- `/meetings/:id` and client detail notes
- Edit forms: hint under the notes textarea

## Files

- `frontend/src/markdown/MarkdownBody.tsx`
- `frontend/src/pages/MeetingDetailPage.tsx`
- `frontend/src/pages/ClientDetailPage.tsx`
- `frontend/src/pages/MeetingFormPage.tsx`
- `frontend/src/pages/ClientFormPage.tsx`

## Follow-ups / out of scope

No live preview in the form. No syntax highlighting.
