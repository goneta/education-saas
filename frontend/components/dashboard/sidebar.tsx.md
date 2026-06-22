# sidebar.tsx

## Source File

- `frontend/components/dashboard/sidebar.tsx`

## Purpose

- Owns dashboard navigation, collapsible module groups, and the bottom user account menu.
- Exposes localized account destinations for overview, renewals, security, sessions, contact, payments, credit, invoices, preferences, notifications, team members, and referrals.

## DOX Scope

- Nearest contract: `frontend/components/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Account labels must use the `account` translation namespace.
- Preserve independent sidebar scrolling and dark-mode readability.
- The active route uses the same dark surface as the hover state and keeps icons/text high contrast.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
