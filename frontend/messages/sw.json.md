# sw.json

## Source File

- `frontend/messages/sw.json`

## Purpose

- JSON configuration, catalog, or structured data file. It contributes localized UI copy.

## DOX Scope

- Nearest contract: `frontend/messages/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m json.tool frontend\messages\<locale>.json; npm run build
