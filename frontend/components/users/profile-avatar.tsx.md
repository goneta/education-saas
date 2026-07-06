# profile-avatar.tsx

## Purpose

- Renders a tenant-authorized user profile photo or initials fallback.
- Allows authorized users to upload PNG, JPEG, or WebP profile photos up to 2 MB.
- Fetches protected photo bytes with the active bearer token instead of exposing file URLs publicly.

## Verification

- Run targeted ESLint and the frontend build.
- The avatar button carries `data-teducai-ignore="true"` so the table enhancer's action-cell detection skips it. Without it, the button title "Modifier la photo de profil" matched the enhancer's /modifier|edit|.../ action regex, so it hid the whole name cell and shifted every column left in the students/teachers lists.
