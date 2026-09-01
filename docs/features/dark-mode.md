# Feature: Dark mode

Date: 2026-09-01

## What it does

Staff can switch the CRM between light and dark. Preference is stored in the browser. Public invoice links and print stay light.

## Behavior

- Toggle lives in the account menu (click your name in the sidebar).
- Choice is stored in `localStorage` key `m2_theme` (`light` or `dark`). Default is **light**.
- `html.dark` remaps `ink` (text) and `paper` (cards). Page background is set on `body`. `cream` and `navy` stay put so sidebar and primary buttons keep light-on-navy contrast.
- A small script in `index.html` applies the class before React loads so the page does not flash light on refresh.
- Public `/i/:token` wraps in `.force-light` so clients always see a light document.
- Print still forces a white page.

## API

None.

## UI

- Sidebar → your name → **Dark mode** switch

## Files

- `frontend/src/index.css`
- `frontend/src/theme/ThemeContext.tsx`
- `frontend/src/layouts/StaffLayout.tsx`
- `frontend/index.html`
- `frontend/src/pages/PublicInvoicePage.tsx`

## Follow-ups / out of scope

No `prefers-color-scheme` follow. No per-user server setting.
