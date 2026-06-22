# pdf.py

## Source File

- `backend/pdf.py`

## Purpose

- Generates branded school PDFs with a common identity header, optional logo image, structured content, and QR verification payload.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Callers should pass the shared school header payload for official school documents.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
