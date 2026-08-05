# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/education/classes/page.tsx`

## Purpose

- React/Next.js TypeScript component or page file. It participates in Next.js App Router routing.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Class deletion uses the shared TeducAI confirmation dialog instead of a browser prompt.
- The class list stays visible, uses French labels, and applies readable dark header, row, border, hover, and action styles.

- Record tables use the shared universal `TableFilter` / `useTableFilter` (column selector + debounced accent/case-insensitive search-as-you-type, persisted per `storageKey`); reuse it for any new collection rather than bespoke search inputs.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
- #1/#6: class list has a **Nb Élèves** column (count per class from `/education/classes/{id}/students`) and a Users action opening a modal with a scrollable students table (Nom complet / Âge / Sexe), each row clickable to the student profile (`/dashboard/students/{user_id}`).
- Niveau: champ texte libre remplacé par un Select alimenté par /reference-data/school_level (référentiel global + niveaux locaux de l établissement), gate RequireOptions (« Ajouter un niveau » → reference-data) + submit désactivé tant qu aucun niveau n existe; la valeur legacy d une classe existante reste sélectionnable.
