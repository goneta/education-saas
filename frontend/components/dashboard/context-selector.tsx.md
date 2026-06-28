# context-selector.tsx

## Purpose

- Displays the authorized organization, school, school-model assignment, and academic-year context in the dashboard header.
- Consumes the shared `WorkingContextProvider` (`useWorkingContext`) for options/active/`setContext`; no longer fetches independently.
- Dropdown has a search-as-you-type field (accent/case-insensitive via `lib/normalize`) over the accessible institution/model assignments, then an academic-year select; closes on outside click / Escape.
- When no context is active yet but assignments exist, shows a "Select working context" affordance so the admin can bootstrap the initial context. Persists through `setContext`, which stores only validated IDs locally and reloads model-scoped data.

## Security

- Options come exclusively from the authenticated backend.
- The backend validates every selected assignment and academic year before persistence.
