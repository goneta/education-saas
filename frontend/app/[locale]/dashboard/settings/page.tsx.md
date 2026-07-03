# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/settings/page.tsx`

## Purpose

- Provides persistent school profile/logo editing, subscription management, user administration, role/permission management, localization, templates, and audit views.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- School data is reloaded after save; logos use secure multipart upload instead of React-only data URLs.
- Paid plans remain pending until provider confirmation, while Free activates immediately.
- The subscription payment-history / invoices tables are laid out one per row (full width), not two-up, for readability across breakpoints. Config forms and stat grids are unchanged.
- User edit/delete actions use tenant-aware backend APIs and TeducAI dialogs.
- The logo preview is dark-mode safe, clickable in edit mode, supports replacement/deletion, and reloads persisted server state.
- Subscription plan cards remain readable in both themes and paid plans continue through the confirmation/payment workflow.
- Administrators can activate multiple school models and initialize assignment-scoped reference data without duplicates.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
- Security: the user-creation form no longer pre-fills a hardcoded default password.
