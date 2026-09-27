# Scratch: Staff password recovery

## Status
promoted

## Linked input
docs/input/2026-09-27-admin-password-reset.md

## Session notes (append newest at bottom)

### 2026-09-27 14:05 — turn summary
- **User:** We need to add a password recovery.
- **Agent:** Current auth is staff-only JWT + bcrypt. Signed-in staff can change password (`POST /api/auth/password`) if they know the current one. Feature doc lists password-reset email as out of scope. No mailer in the app. Only a few seed staff accounts.
- **Open threads:** Who is locked out (self vs admin)? How is the new password delivered if there is no email? Token lifetime and enumeration?

## Raw bullets
- Today: `/login` + account settings “Change password” (current + new, min 8).
- No forgot-password route, no reset token table, no SMTP.
- Public invoice links are unguessable URLs, not accounts. Recovery is staff-only.
- Seed users are real Gmail addresses (`SEED_EMAIL`).

## Risks / dumb ideas / maybes
- Email reset without a mailer is a new subsystem (SMTP, secrets, deliverability), not a form.
- Admin-sets-password while logged in is smaller and matches a two-person team.
- Must not reveal whether an email is a staff account.
- Reset links that never expire, or that stay valid after use, are a lockout/account-takeover hole.
- Showing a temporary password on screen is fine for an admin reset; emailing it in cleartext is worse than a one-time link.

### 2026-09-27 14:07 — turn summary
- **User:** Can we just use a script instead?
- **Agent:** Yes for this staff size. A CLI that bcrypt-hashes a new password and updates `users.password_hash` by email. Run from the host against `crm` or `crm_dev`. No mailer, no login UI, no token table. Changing `SEED_PASSWORD` does not reset existing users.
- **Open threads:** Prod only or both DBs? Operator types the new password, or the script prints a one-time random one? Still no way to invalidate existing JWTs.

## Raw bullets (script variant)
- Fits: two staff, shell access already equals DB access.
- Must call the same bcrypt helper as login (`hash_password`), not store plaintext.
- Target DB is explicit (`crm` vs `crm_dev`). Wrong DB is a silent no-op or a prod surprise.
- Unknown email should fail loudly for the operator (this is not a public endpoint).
- Existing sessions stay valid until JWT expiry. No revocation list today.

### 2026-09-27 14:12 — turn summary
- **User:** `admin@m2solution.ca` should have a screen to reset a password: fill in the username and the new password for that account.
- **Agent:** There is no admin role and no username. Every staff user is equal. Login identity is email. `admin@m2solution.ca` is not a user. The old seed `admin@m2solution.com` is explicitly ignored; seeds are two Gmail addresses.
- **Open threads:** Create `admin@m2solution.ca` or did they mean an existing person? Target field is email? Confirm new password twice? Hardcoded allowlist of one email?

## Raw bullets (admin UI variant)
- Signed-in `admin@m2solution.ca` only sees “Reset password”.
- Form: target account + new password. Sets `password_hash` for that user.
- Other staff never see the control. API must enforce the same check, not only hide the button.
- If that admin account is itself locked out, this UI cannot help. A script remains the break-glass.
- Target’s existing JWT stays valid until expiry.

### 2026-09-27 14:14 — turn summary
- **User:** Correction: the account is `admin@m2solution.com`. Later they want to change the seed password and the seed email. Not part of this change.
- **Agent:** That address is hard-coded as the old seed and is ignored. If `SEED_EMAIL` is exactly `admin@m2solution.com`, startup seeds the two Gmail accounts instead and does not create the admin user. Privilege tied to that email will not follow a future seed-email change.
- **Open threads:** Does `admin@m2solution.com` already exist in the database? Lock this UI now and park seed email/password for a later capture?

## Raw bullets (correction)
- Admin identity: `admin@m2solution.com` (not `.ca`).
- Form target stays the other staff member’s email. There is still no username.
- Seed email and seed password change is a later, separate idea. Do not bundle it.
- Risk: current code treats `admin@m2solution.com` as “unset” and will not seed it.

### 2026-09-27 14:15 — turn summary
- **User:** Yes, `admin@m2solution.com` already exists.
- **Agent:** Promoted the locked direction to `docs/input/2026-09-27-admin-password-reset.md` (status draft). Seed email/password change stays out of scope. Asking gate 1.
- **Open threads:** Gate 1 not approved. Self-reset and “new password must differ” left as defaults in the input doc.
