# Admin password reset

## Status
ready-for-github

## Change type
feature

## Summary
Signed-in `admin@m2solution.com` can set a new password for another staff account by entering that account’s email and the new password. No email is sent. No public forgot-password page.

## Motivation
Staff who forget a password can only change it today if they still know the current one (`POST /api/auth/password`). There is no mailer. The operator account `admin@m2solution.com` already exists and can sign in, so recovery should be an action on that account.

## Detailed intent
- Only `admin@m2solution.com` sees a **Reset password** control, and only while signed in.
- The API enforces the same check. Hiding the button is not the authorization.
- The form fields are the **target staff email** and the **new password**, entered twice.
- New password rules match the existing change-password flow: minimum 8 characters, maximum 72.
- Unknown email returns an error to the admin (this is not a public endpoint).
- Success replaces `password_hash` using the same bcrypt helper as login.
- Other staff keep “change my own password”, which still requires the current password.
- `admin@m2solution.com` is not created by this change. The user confirmed the account already exists and can sign in.
- The app currently treats `SEED_EMAIL=admin@m2solution.com` as unset and seeds two Gmail addresses instead. This feature must not undo that rule and must not depend on the seeder creating the admin user.

## Constraints
- Staff-only. No client accounts.
- No SMTP, no reset links, no new role model.
- Privilege is the literal email `admin@m2solution.com`, not “whoever is listed in `SEED_EMAIL`”.
- There is no username column. The target identifier is the staff email.
- Existing JWTs stay valid until they expire. This change does not add session revocation.

## Open questions
- Whether the admin may reset their own password through this form (bypassing the current-password check). Default if unanswered: allow it, since they are already authenticated as that account.
- Whether a reset should be refused when the new password equals the current one. Default if unanswered: same rule as self-service change — refuse.

## Risks and criticism
- Anyone who can sign in as `admin@m2solution.com` can set any staff password. That is the point of the feature and also the whole security boundary.
- If that account is locked out, this screen cannot help. Break-glass stays a later server-side action, not this change.
- A future change of `SEED_EMAIL` or `SEED_PASSWORD` will not move this privilege and will not update an existing password hash.
- The seeder still ignores `admin@m2solution.com`. If that user is ever deleted, this UI disappears and startup will not recreate it while the ignore rule stands.
- The target’s existing session keeps working until the JWT expires (7 days by default).

## Out of scope
- Forgot-password link on `/login`.
- Email delivery of a reset link or a temporary password.
- Operator shell script.
- Changing `SEED_EMAIL` or `SEED_PASSWORD`, or renaming the admin account. The user wants that later, as its own change.
- Roles, invites, or kicking existing sessions out.
- Creating `admin@m2solution.com` if it is missing.

## Technical plan (draft)
- New staff endpoint, authenticated, allowed only when `current_user.email` is `admin@m2solution.com`.
- Body: target email, new password. Hash and save. 404 or 400 when the email is not a user.
- UI in the existing account area (sidebar account settings), rendered only for that email.
- Docs: update `docs/features/auth.md` in the same change.

## Proposed issues (draft)
Left for GitHub decomposition after gate 1. One feature: admin-only reset of another staff password. Not split here.

## Raw notes
- Brainstorm: `docs/brain-storming/2026-09-27-password-recovery.md`
- User correction: `admin@m2solution.com`, not `.ca`.
- User confirmed that account already exists.
- Seed email and seed password changes are explicitly later.
