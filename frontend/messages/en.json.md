# en.json

## Source File

- `frontend/messages/en.json`

## Purpose

- JSON configuration, catalog, or structured data file. It contributes localized UI copy.

## DOX Scope

- Nearest contract: `frontend/messages/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Includes the `layout` working-context keys (workingContext, contextSearchPlaceholder, contextNoResults, selectContext, academicYear, currentYear, contextRequiredTitle/Message) and the `filters` namespace (column, allColumns, searchPlaceholder, noResults); keep these in parity across en/fr/es/sw.

## Verification

- python -m json.tool frontend\messages\<locale>.json; npm run build
- Includes the `navigation` Smart Transport keys (smartTransport, transportDashboard, drivers, vehicles, routes, transportAssignments); keep parity across en/fr/es/sw.
