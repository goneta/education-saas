# Purpose

- Own translation catalogs for supported languages.

# Ownership

- `fr.json`, `en.json`, `es.json`, `sw.json`.

# Local Contracts

- French is the default product language.
- Add equivalent keys across all supported locale files when adding navigational or shared UI text.
- Keep JSON valid and avoid leaving English text in the French catalog unless it is a product name or intentional technical label.

# Work Guidance

- Prefer concise labels that fit mobile navigation and buttons.
- Keep terminology consistent across finance, school operations, AI, and settings modules.

# Verification

- JSON parse check is covered by `npm run build`.
- Targeted validation can use `python -m json.tool frontend\\messages\\fr.json`.

# Child DOX Index

- No child AGENTS.md files yet.
