# Scratch: Google sign-in for staff

## Status
promoted

## Linked input
docs/input/2026-09-27-google-sign-in.md

## Session notes (append newest at bottom)

### 2026-09-27 14:59 — turn summary
- **User:** Would it be easy to add authentication with Google instead of a login account — use my Google account, or other?
- **Agent:** Medium, not a rewrite. Login today is staff-only email + bcrypt; the rest of the app only sees a JWT. Google can be a second way to mint that JWT for emails that already exist in `users`. Replacing passwords, or accepting any Google account, or adding “other” providers, is a different and larger idea.
- **Open threads:** Keep password login beside Google, or remove it? Allowlist existing staff only, or any Google user? What does “or other” mean?

### 2026-09-27 15:00 — turn summary
- **User:** I want both login.
- **Agent:** Password form stays. Google is an extra button that mints the same JWT. Still open: only existing staff emails, and whether a second provider is in scope.
- **Open threads:** Allowlist vs any Google account. Google only, or another provider too?

### 2026-09-27 15:01 — turn summary
- **User:** So I can login with my Google account or local account.
- **Agent:** Same person, two ways in. Local email/password stays. Google works when that Google email is already the staff row. No second provider. Still need an explicit yes that unknown Google accounts are rejected, then we can lock the write-up.
- **Open threads:** Confirm allowlist (existing staff email only). Lock for docs/input?

### 2026-09-27 15:02 — turn summary
- **User:** How would I do this when the Google email is already a staff account?
- **Agent:** You do not link anything by hand. Google returns a verified email; the API looks up `users.email`. Today the two seed staff rows are already those Gmail addresses, so signing in with that Google account is the match. A different Google address fails until that address exists as a staff row. There is no “change my email” or “connect Google” screen today.
- **Open threads:** Same-email match only, or a later “connect a different Google account” action? Lock the write-up?

### 2026-09-27 15:03 — turn summary
- **User:** okay
- **Agent:** Treated that as acceptance of the same-email match. Promoted to `docs/input/2026-09-27-google-sign-in.md` (status draft). Gate 1 not asked as a yes yet in the prior turn; asking now.
- **Open threads:** Gate 1 — create GitHub issues from the draft?

## Raw bullets
- Auth: `POST /api/auth/login` checks email + bcrypt, returns JWT. `users` has `email`, `password_hash`, `full_name`. No OAuth columns.
- Seed staff are already Gmail (`matcote111@gmail.com`, `mathieu.laureti@gmail.com`).
- Public invoices stay token URLs. This is staff login only.
- “Easy” version: “Sign in with Google” button, verify Google ID token, match verified email to an existing user, issue the same JWT. No new accounts.
- Not easy if: drop passwords entirely, open signup to any Google account, or add Microsoft/Apple/generic OIDC in the same change.
- Needs a Google Cloud OAuth client, client secret in env, exact redirect URIs for `https://crm.m2solution.ca` and dev.

## Risks / dumb ideas / maybes
- Any-Google-account signup would let a stranger into the CRM. Allowlist only.
- Removing passwords means a Google outage or an email mismatch locks everyone out. Admin password reset becomes useless.
- Google email change does not update `users.email`; that person would fail the match.
- “Or other” without naming a second provider is scope creep.
