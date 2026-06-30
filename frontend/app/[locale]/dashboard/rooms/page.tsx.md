# page.tsx
## Source File
- `frontend/app/[locale]/dashboard/rooms/page.tsx`
## Purpose
- Rooms management (#5/#6): create rooms (building+name+capacity+type), list with a **Nb Classes** column, **Voir** modal (classes + level from `/facilities/rooms/{id}/classes`), delete (409 when used in a timetable). i18n via `facilities`.
## Maintenance Notes
- Capacity feeds the timetable class>room capacity guard. Nb Classes is fetched per room.
