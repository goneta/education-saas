# add-student-modal.tsx

## Source File

- `frontend/components/students/add-student-modal.tsx`

## Purpose

- Creates students through the canonical `/students` collection endpoint and refreshes the owning list after success.

## DOX Scope

- Nearest contract: `frontend/components/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
- #4: adds an "Informations sur la Classe" section (after Parent/Guardian) — select a niveau (from `/levels?active_only=true`) then a class dynamically filtered to that level (`class.level === level.code`); sends `current_class_id`.
- i18n: uses the shared `studentForm` namespace (FR/EN/ES/SW) — labels, placeholders, gender options, buttons, validation + error messages.
