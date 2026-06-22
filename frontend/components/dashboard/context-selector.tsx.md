# context-selector.tsx

## Purpose

- Displays the authorized organization, school, school-model assignment, and academic-year context in the dashboard header.
- Persists changes through `/context/active`, stores only validated IDs locally, and reloads model-scoped data.

## Security

- Options come exclusively from the authenticated backend.
- The backend validates every selected assignment and academic year before persistence.
