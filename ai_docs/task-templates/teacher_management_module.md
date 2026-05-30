# Task: Implement Teacher Management Module

> **About This Task:** Implement the full Teacher Management module, enabling administrators to manage teacher records. This includes backend API endpoints and a frontend interface for listing, adding, editing, and deleting teachers.

---

## 1. Task Overview

### Task Title
**Title:** Implement Teacher Management System (CRUD)

### Goal Statement
**Goal:** Create a comprehensive system for managing teacher data. This allows school administrators to maintain accurate records of teaching staff, which is essential for future features like class assignment and scheduling. The system will mirror the robust architecture of the Student module.

---

## 2. Project Analysis & Current State

### Technology & Architecture
- **Frameworks:** FastAPI (Backend), Next.js 14+ (Frontend)
- **Language:** Python 3.10+, TypeScript
- **Database:** SQLite (with SQLAlchemy)
- **UI:** shadcn/ui, TailwindCSS
- **Auth:** JWT (RBAC enabled)

### Current State
- **Student Module:** Complete (Reference implementation).
- **Teacher Module:** **Does not exist.** No API endpoints, no frontend pages.
- **Database:** `users` table exists, but likely need a `teachers` table or profile extension. *Correction:* The `users` table handles authentication; a dedicated `teachers` table linked to `users` or standalone (depending on auth strategy) is needed. *Decision:* Teachers are likely Users with a role, but need a specific `teachers` profile table similar to `students`.

---

## 3. Context & Problem Definition

### Problem Statement
Currently, the system cannot store or manage teacher information. There is no way to assign teachers to classes or subjects because the entities do not exist in the database.

### Success Criteria
- [ ] Backend: `teachers` table created via SQLAlchemy migration (or equivalent).
- [ ] Backend: API endpoints for CRUD (`GET`, `POST`, `PUT`, `DELETE` /teachers).
- [ ] Frontend: `dashboard/teachers` page displaying a list of teachers.
- [ ] Frontend: "Add Teacher" modal with validation.
- [ ] Frontend: "Edit Teacher" and "Delete Teacher" functionality.
- [ ] Frontend: Teacher Detail page (optional for Phase 1, but good to have).

---

## 4. Development Mode Context

- **🚨 Project Stage:** Active Development - Phase 1 MVP
- **Priority:** High (Core Data)
- **Data Handling:** New table, no existing data to migrate.

---

## 5. Technical Requirements

### Functional Requirements
- **List Teachers:** Display name, email, specialization/subject, phone, and status.
- **Add Teacher:** Form collecting personal details, contact info, and subjects.
- **Edit Teacher:** Modify existing details.
- **Delete Teacher:** Remove record (soft delete preferred if possible, but hard delete for MVP is acceptable).

### Non-Functional Requirements
- **Consistency:** UI must match the Student module (table layout, modal styles).
- **Performance:** Pagination for list view (backend supports it?).

---

## 6. Data & Database Changes

### Database Schema Changes
**New Table: `teachers`**
```python
class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # If teachers have login
    
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    address = Column(String)
    
    specialization = Column(String) # e.g. "Mathematics", "Science"
    join_date = Column(Date)
    
    is_active = Column(Boolean, default=True)
```
*Note: Depending on the existing User model, we might link `Teacher` to `User` 1:1.*

### Data Model Updates (Frontend)
```typescript
interface Teacher {
  id: number
  first_name: string
  last_name: string
  email: string
  phone: string
  specialization: string
  is_active: boolean
}
```

---

## 7. API & Backend Changes

### Endpoints
- `GET /teachers/` - List all
- `POST /teachers/` - Create new
- `GET /teachers/{id}` - Get specifics
- `PUT /teachers/{id}` - Update
- `DELETE /teachers/{id}` - Delete

---

## 8. Frontend Changes

### New Components
- `components/teachers/teacher-list-table.tsx`
- `components/teachers/add-teacher-modal.tsx`
- `components/teachers/edit-teacher-modal.tsx`
- `components/teachers/delete-teacher-dialog.tsx`

### Page Updates
- `app/[locale]/dashboard/teachers/page.tsx`

---

## 9. Implementation Plan

### Phase 1: Backend Foundation
- [ ] Create `backend/models/teacher.py`
- [ ] Create `backend/schemas/teacher.py` (Pydantic models)
- [ ] Create `backend/crud/crud_teacher.py`
- [ ] Create `backend/routers/teachers.py`
- [ ] Register router in `main.py`
- [ ] Initialize DB / Run Migrations

### Phase 2: Frontend List & Create
- [ ] Create `teachers/page.tsx` (List view)
- [ ] Create `add-teacher-modal.tsx`
- [ ] Integrate `POST` and `GET` APIs

### Phase 3: Update & Delete
- [ ] Create `edit-teacher-modal.tsx`
- [ ] Create `delete-teacher-dialog.tsx`
- [ ] Integrate `PUT` and `DELETE` APIs

### Phase 4: Verification
- [ ] Test full CRUD cycle

---

## 10. Task Completion Tracking

**Phase 1: Backend** - ❌ Not Started
**Phase 2: Frontend List/Create** - ❌ Not Started
**Phase 3: Frontend Edit/Delete** - ❌ Not Started
**Phase 4: Verification** - ❌ Not Started

---

## 11. Custom Rules & Instructions

- **Reuse Patterns:** Copy the pattern from `students` rigorously. Do not invent new UI paradigms.
- **Strict Typing:** Ensure Pydantic schemas match TypeScript interfaces.
