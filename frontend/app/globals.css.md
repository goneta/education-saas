# globals.css

## Source File

- `frontend/app/globals.css`

## Purpose

- Owns shared light/dark tokens and global presentation for pages, cards, tables, forms, dialogs, menus, status surfaces, and scrollbars.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Dark mode should rely on shared variables and selectors instead of route-specific overrides.
- Global selectors cover legacy near-white card colors, bordered rounded surfaces, forms, tables, and section containers so opened content never becomes white-on-white.
- Table headers, rows, inputs, selects, dialogs, legacy utility colors, disabled states, and hover states share explicit dark-mode contrast rules.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
