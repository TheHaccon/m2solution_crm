# Staff Google sign-in beside password login

## Status
ready-for-github

## Change type
feature

## Summary
Staff can sign in with the existing email and password form, or with Google. Google succeeds only when Google’s verified email already equals a row in `users`. Both paths issue the same staff JWT. Unknown Google accounts are rejected and no user is created.

## Motivation
The two seeded staff addresses are already Gmail accounts. Signing in with that Google account should be enough, while the local password remains a fallback when Google is unavailable.

## Detailed intent
- `/login` keeps the email and password form and adds a **Sign in with Google** button.
- Choosing Google sends the user to Google and back. The API trusts only a verified email from Google.
- Lookup is `users.email` equal to that address (case-insensitive, same as password login).
- A match returns `{ access_token }` for that existing user. The rest of the app is unchanged.
- No match returns an error. The API does not insert a user, does not add them to a team, and does not reveal whether other emails exist beyond a generic failure.
- Password login, change-password, and admin password reset stay as they are.
- Seed staff today are `matcote111@gmail.com` and `mathieu.laureti@gmail.com`. Those addresses work with Google only because they are already staff rows, not because they are Gmail in general.

## Constraints
- Staff only. Public invoice links stay unauthenticated token URLs.
- No second provider (Microsoft, Apple, generic OIDC).
- No “connect a different Google account” screen. The Google address and the staff email must be the same string.
- There is no UI to change a staff email. A Google address that is not already in `users` cannot be attached from the login page.
- Google OAuth client id and secret live in environment config. Redirect URLs must include production `https://crm.m2solution.ca` and the dev origin.
- Someone must create that OAuth client in Google Cloud before the button can succeed. The app cannot invent those credentials.

## Open questions
- None that block the direction. Operator setup of the Google Cloud OAuth client is required before the feature can be tried, and is outside the repo.

## Risks and criticism
- A Google account that is not already staff must be rejected. Accepting any Google user would open the CRM to strangers.
- If Google changes the account’s email, sign-in with Google fails until `users.email` is updated. Nothing in the app does that update today.
- Removing the password form is out of scope on purpose. A Google outage or a mismatched email would otherwise lock everyone out, and admin password reset would not help.
- The client secret and redirect URLs are easy to mis-set. A wrong redirect makes the button fail even when the email would have matched.
- This does not revoke existing JWTs and does not add a new role.

## Out of scope
- Replacing or removing email/password login.
- Creating staff users from Google.
- Linking a Google account whose email differs from `users.email`.
- Microsoft, Apple, or other providers.
- Forgot-password email, invites, or changing `SEED_EMAIL`.
- Client portal accounts.

## Technical plan (draft)
- New staff login path that verifies Google’s token or auth code, reads the verified email, loads `User` by that email, and calls the existing JWT helper.
- Login page button next to the current form.
- Env vars for the Google client id, secret, and allowed redirect. Document them in `docs/features/auth.md`, `docs/run.md`, and `docs/architecture.md` in the same change.
- No new account-linking table in this version. Email match is the whole link.

## Proposed issues (draft)
Left for GitHub decomposition after gate 1. One feature: Google as a second staff login that only matches existing emails.

## Raw notes
- Brainstorm: `docs/brain-storming/2026-09-27-google-sign-in.md`
- User: both logins; “I can login with my Google account or local account”; accepted that they do not link accounts by hand.
