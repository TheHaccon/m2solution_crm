# Delivery: Dev reseed and seed-data discipline (#26)

## Summary

Adds `python -m app.seeds` / `./scripts/dev-reseed.sh` to wipe and repopulate **crm_dev** with demo data, a Cursor rule for keeping seeds in sync with features, and removes the `admin@m2solution.com` gate on staff password reset (any staff may reset).

## Verification

- `python scripts_test_admin_password_reset.py`
- `python scripts_test_dev_reseed.py` (when `DATABASE_URL` targets `crm_dev`)

## PR

Fixes #26
