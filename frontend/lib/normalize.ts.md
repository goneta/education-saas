# normalize.ts

## Purpose

- Shared accent- and case-insensitive text normalization (`normalizeText`) and substring matching (`matchesText`) for all search-as-you-type inputs.
- Used by the global institution context selector and the universal `TableFilter` so search behaves identically everywhere (folds diacritics, lowercases, trims).

## Maintenance Notes

- Keep this dependency-free and pure; it runs on every keystroke over potentially large lists.
- If new search surfaces are added, reuse these helpers instead of re-implementing case/accent folding.
