# Feature: File manager

Date: 2026-09-01

## What it does

Staff get a **Files** sidebar page with a folder tree. The **Team** root is shared with the active team (configs, uploads). **Personal** is private to the signed-in user. Files live on disk; metadata is in Postgres. There is no public URL.

## Behavior

- Staff JWT required. Clients cannot see files.
- Opening **Personal** creates **Invoices** and **Expenses** folders if they are missing. **Expenses** also gets a subfolder per expense category (Gas, Purchase, …).
- Creating, editing, sending, marking paid, or voiding an invoice writes `{number}.pdf` into that personal folder (overwrites the same file). Deleting a **draft** also deletes its PDF.
- Expense receipts are stored in Personal → **Expenses** → **{category}** as `expense-{id}-{filename}`.
- Team listing and writes require `X-Team-Id` and membership. Personal files ignore the team header and filter by `owner_id`.
- Create folders, create empty text/markdown/json configs, upload any file up to **25 MB**, rename, move, download, delete (folders delete recursively).
- Preview: markdown via the same renderer as meeting notes, other text in a monospace block (editable), images inline, **PDFs** in the right pane. Everything else is download-only.
- Names cannot contain `/`, `\`, or `..`. Duplicate names in the same folder return **409**.
- Blobs are stored as `FILES_ROOT/<uuid>` — never a user-supplied path. Prod and dev use **different** host directories so the two stacks do not share files.
- The Postgres replica does **not** copy these files. They sit on the primary data disk (`/mnt/data_main/...` by default).

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET | `/api/files?space=team\|personal` | staff | Flat list; UI builds the tree |
| POST | `/api/files/folders` | staff | JSON `{ name, parent_id, space }` |
| POST | `/api/files/text` | staff | JSON `{ name, parent_id, space, content }` |
| POST | `/api/files/upload` | staff | Multipart `space`, `parent_id`, `file` |
| GET | `/api/files/{id}` | staff | Metadata |
| GET | `/api/files/{id}/content` | staff | Bytes; `?download=1` forces attachment |
| PUT | `/api/files/{id}/content` | staff | JSON `{ content }` for text files only |
| PATCH | `/api/files/{id}` | staff | Rename / move `{ name, parent_id }` |
| DELETE | `/api/files/{id}` | staff | Recursive for folders; 204 |

Unknown or out-of-scope ids return **404** (not 403).

## UI

- Sidebar **Files** → `/files`
- Left: Team (active team name) and Personal trees
- Right: folder listing or file preview
- New folder, New file, Upload, Rename, Delete, Download, Edit/Save for text

## Files

- `backend/app/models/file.py`
- `backend/app/api/files.py`
- `backend/app/schemas/file.py`
- `backend/app/services/file_storage.py`
- `backend/app/services/invoice_files.py`
- `backend/app/services/invoice_pdf.py`
- `backend/app/services/expense_files.py`
- `backend/alembic/versions/003_files.py`
- `frontend/src/pages/FilesPage.tsx`
- `frontend/src/layouts/StaffLayout.tsx`
- `docker-compose.yml`, `docker-compose.dev.yml`, `frontend/nginx.conf`

## Follow-ups / out of scope

Google Drive sync (OAuth, folder mapping, two-way sync). `storage_backend` is `local` and `FileStorage` is the swap point. Also out of v1: quotas, versioning, trash, public share links, multi-file drag-and-drop.
