# Task: Complete Student Management Module

> **About This Task:** Complete the Student Management module by adding edit, delete, and detail view functionality. This will make the student management feature production-ready and fully functional.

---

## 1. Task Overview

### Task Title
**Title:** Complete Student Management Module - Add Edit, Delete, and Detail View

### Goal Statement
**Goal:** Transform the Student Management module from 70% complete to 100% production-ready by implementing edit student functionality, delete student functionality, and a detailed student profile view. This will enable school administrators to fully manage student records through an intuitive interface, completing one of the core Phase 1 modules from the PRD.

---

## 2. Project Analysis & Current State

### Technology & Architecture
- **Frontend Framework:** Next.js 14+ with App Router
- **Language:** TypeScript
- **Database & ORM:** SQLite (dev) with SQLAlchemy ORM
- **UI & Styling:** shadcn/ui components + TailwindCSS
- **Authentication:** JWT-based authentication (complete)
- **Key Architectural Patterns:** 
  - Multi-tenancy (school-scoped data)
  - RBAC (Role-Based Access Control)
  - RESTful API design

### Current State
**Backend (100% Complete):**
- ✅ `POST /students/` - Create student
- ✅ `GET /students/` - List students (with filtering)
- ✅ `GET /students/{id}` - Get single student
- ✅ `PUT /students/{id}` - Update student (READY TO USE)
- ✅ `DELETE /students/{id}` - Delete student (READY TO USE)

**Frontend (70% Complete):**
- ✅ Students list page with table display
- ✅ Search/filter functionality
- ✅ Add Student modal (fully functional)
- ❌ Edit Student modal (NOT IMPLEMENTED)
- ❌ Delete confirmation dialog (NOT IMPLEMENTED)
- ❌ Student detail/profile page (NOT IMPLEMENTED)
- ❌ Edit/Delete buttons have no onClick handlers

**Current Issues:**
- Edit and Delete buttons in table are decorative only (no onClick handlers)
- No way to view full student details
- No way to update student information
- No way to remove students from the system

---

## 3. Context & Problem Definition

### Problem Statement
School administrators can add students but cannot edit their information, view detailed profiles, or remove students from the system. This makes the feature incomplete and not production-ready. Users need full CRUD (Create, Read, Update, Delete) capabilities to manage student records effectively.

### Success Criteria
- [ ] Users can click "Edit" button and update student information
- [ ] Users can click "Delete" button and remove students (with confirmation)
- [ ] Users can click on a student row to view detailed profile
- [ ] All operations work correctly with the backend API
- [ ] Visual design matches `dashboard_visual_description.md`
- [ ] All changes are scoped to the user's school (multi-tenancy)
- [ ] Proper error handling and loading states
- [ ] Student list refreshes after edit/delete operations

---

## 4. Development Mode Context
- **🚨 Project Stage:** Active Development - Phase 1 MVP
- **Breaking Changes:** None - adding new features only
- **Data Handling:** Must preserve existing student data
- **User Base:** School administrators and super admins
- **Priority:** High - blocking completion of Phase 1 core module

---

## 5. Technical Requirements

### Functional Requirements

#### 1. Edit Student Functionality
- User can click "Edit" button on any student row
- Edit modal opens with student data pre-filled
- User can modify: name, email, registration number, date of birth, gender, addresses, parent info
- User can save changes → API call to `PUT /students/{id}`
- Success: Modal closes, student list refreshes, success message shown
- Error: Error message displayed, modal stays open

#### 2. Delete Student Functionality
- User can click "Delete" button on any student row
- Confirmation dialog appears: "Are you sure you want to delete [Student Name]?"
- User confirms → API call to `DELETE /students/{id}`
- Success: Student removed from list, success message shown
- User cancels → Dialog closes, no action taken
- Error: Error message displayed

#### 3. Student Detail View
- User can click on student row to view full profile
- Navigate to `/dashboard/students/{id}` page
- Display all student information in organized sections:
  - Personal Information (name, email, registration number, DOB, gender)
  - Contact Information (student address)
  - Parent/Guardian Information (name, phone, email, address)
  - Academic Information (current class, enrollment date)
- "Edit" and "Delete" buttons available on detail page
- "Back to Students" navigation

### Non-Functional Requirements
- **Performance:** Edit/delete operations complete within 2 seconds
- **Security:** All operations require authentication, scoped to user's school
- **Usability:** Clear confirmation dialogs, intuitive navigation, helpful error messages
- **Responsive Design:** All components work on mobile, tablet, and desktop
- **Theme Support:** Follow existing design system (white cards, #111827 text, etc.)

### Technical Constraints
- Must use existing backend API endpoints (no backend changes)
- Must maintain visual design consistency
- Must not break existing "Add Student" functionality
- Must work with Next.js App Router and locale routing
- Must use existing shadcn/ui components

---

## 6. Data & Database Changes

### Database Schema Changes
**None** - Backend schema is complete and supports all operations.

### Data Model Updates
**TypeScript Types (Frontend):**
```typescript
// Already exists in add-student-modal.tsx, reuse or extract to types file
interface Student {
  id: number
  email: string
  full_name: string
  role: string
  school_id: number
  is_active: boolean
  student_profile: {
    registration_number: string
    date_of_birth: string
    gender: string
    student_address: string
    parent_name: string
    parent_phone: string
    parent_email: string
    parent_address: string
    current_class_id: number | null
  }
}
```

### Data Migration Plan
**None** - No data migration needed.

---

## 7. API & Backend Changes

### Backend Endpoints (Already Exist - No Changes Needed)
- `PUT /students/{id}` - Update student
- `DELETE /students/{id}` - Delete student
- `GET /students/{id}` - Get student details

**Request/Response Examples:**

**Update Student:**
```typescript
PUT /students/123
Headers: { Authorization: "Bearer {token}" }
Body: {
  full_name: "Updated Name",
  email: "updated@email.com",
  profile: {
    registration_number: "STU-2024-001",
    date_of_birth: "2010-01-15",
    gender: "M",
    student_address: "123 Main St",
    parent_name: "John Doe Sr.",
    parent_phone: "+1234567890",
    parent_email: "parent@email.com",
    parent_address: "123 Main St"
  }
}
```

**Delete Student:**
```typescript
DELETE /students/123
Headers: { Authorization: "Bearer {token}" }
Response: 204 No Content
```

---

## 8. Frontend Changes

### New Components to Create

#### 1. `components/students/edit-student-modal.tsx`
**Purpose:** Modal for editing student information
**Features:**
- Reuse form structure from AddStudentModal
- Pre-fill form with existing student data
- Submit to `PUT /students/{id}`
- Validation and error handling
- Loading states

#### 2. `components/students/delete-student-dialog.tsx`
**Purpose:** Confirmation dialog for deleting students
**Features:**
- Show student name in confirmation message
- "Cancel" and "Delete" buttons
- Call `DELETE /students/{id}` on confirm
- Loading state during deletion
- Error handling

#### 3. `app/[locale]/dashboard/students/[id]/page.tsx`
**Purpose:** Student detail/profile page
**Features:**
- Fetch student data from `GET /students/{id}`
- Display all student information in organized sections
- Edit and Delete buttons
- Back navigation
- Loading and error states

### Modified Components

#### `app/[locale]/dashboard/students/page.tsx`
**Changes:**
- Replace mock data with real API calls to `GET /students/`
- Add onClick handlers to Edit and Delete buttons
- Add state for edit modal and delete dialog
- Add row click handler to navigate to detail page
- Implement data refresh after edit/delete

---

## 9. Implementation Plan

### Phase 1: Fetch Real Student Data
**Tasks:**
- [ ] Update `students/page.tsx` to fetch from API instead of mock data
- [ ] Add loading state while fetching
- [ ] Add error handling for API failures
- [ ] Implement data refresh mechanism

### Phase 2: Delete Functionality
**Tasks:**
- [ ] Create `delete-student-dialog.tsx` component
- [ ] Add delete dialog state to students page
- [ ] Connect Delete button onClick to open dialog
- [ ] Implement API call to `DELETE /students/{id}`
- [ ] Refresh student list after successful deletion
- [ ] Add success/error toast notifications

### Phase 3: Edit Functionality
**Tasks:**
- [ ] Create `edit-student-modal.tsx` component (based on add-student-modal)
- [ ] Add edit modal state to students page
- [ ] Connect Edit button onClick to open modal with student data
- [ ] Implement API call to `PUT /students/{id}`
- [ ] Refresh student list after successful edit
- [ ] Add success/error toast notifications

### Phase 4: Student Detail Page
**Tasks:**
- [ ] Create `students/[id]/page.tsx` dynamic route
- [ ] Fetch student data using student ID from URL
- [ ] Design and implement profile layout
- [ ] Add Edit and Delete buttons on detail page
- [ ] Add back navigation
- [ ] Make table rows clickable to navigate to detail page

### Phase 5: Testing & Polish
**Tasks:**
- [ ] Test edit flow end-to-end in browser
- [ ] Test delete flow with confirmation
- [ ] Test detail page navigation
- [ ] Test error scenarios (network errors, 404, etc.)
- [ ] Verify visual design matches reference
- [ ] Test on mobile/tablet
- [ ] Verify multi-tenancy (can only see/edit own school's students)

---

## 10. Task Completion Tracking

### Real-Time Progress Tracking
Update this section as tasks are completed:

**Phase 1: Fetch Real Data** - ❌ Not Started
**Phase 2: Delete Functionality** - ❌ Not Started
**Phase 3: Edit Functionality** - ❌ Not Started
**Phase 4: Detail Page** - ❌ Not Started
**Phase 5: Testing** - ❌ Not Started

---

## 11. File Structure & Organization

### New Files to Create
```
frontend/
  components/
    students/
      edit-student-modal.tsx          [NEW]
      delete-student-dialog.tsx       [NEW]
  app/
    [locale]/
      dashboard/
        students/
          [id]/
            page.tsx                   [NEW]
```

### Files to Modify
```
frontend/
  app/
    [locale]/
      dashboard/
        students/
          page.tsx                     [MODIFY - Add real API calls, handlers]
```

---

## 12. AI Agent Instructions

### Implementation Workflow
🎯 **MANDATORY PROCESS:**

**Rule Management:**
- When you create a new rule in `ai_docs/rules/`, you MUST immediately update `ai_task_template_skeleton.md`

**Task Creation:**
- This task was created using `ai_task_template_skeleton.md` as the base template

**Task Execution:**
- Use THIS file as the source of truth during implementation
- Follow all rules and checklists defined below
- Update task progress as you work

**Project-Specific Requirements:**
- Fetch real student data from API (not mock data)
- Implement all CRUD operations
- Follow visual design system strictly
- Test in browser before declaring complete

### Communication Preferences
- Report progress after each phase completion
- Ask for clarification if API responses don't match expectations
- Notify user of any blocking issues immediately

### Code Quality Standards
- Use TypeScript with proper typing
- Follow existing code patterns from add-student-modal
- Add proper error handling for all API calls
- Include loading states for better UX
- Write clean, readable code with comments where needed

---

## 13. Second-Order Impact Analysis

### Impact Assessment

**Potential Breaking Points:**
- Students page API integration might reveal auth token issues
- Delete operation might fail if student has related records (grades, attendance)
- Edit operation might conflict with unique constraints (email, registration number)

**Performance Concerns:**
- Student list might be slow with many students (consider pagination in future)
- Detail page loads student data separately (acceptable for now)

**User Workflow Impacts:**
- Users will now have complete student management capabilities
- Workflow becomes: Add → View → Edit → Delete (full lifecycle)
- Must ensure data consistency across all operations

---

## 14. Mandatory Rules & Best Practices

> **📋 CRITICAL:** These rules represent lessons learned from past errors. Follow ALL rules during implementation.
> 
> Full rule details are in `ai_docs/rules/` - read the complete files for comprehensive guidance.

### 🚨 Critical Process Rules

#### 1. Auto-Test-Fix Process (MOST IMPORTANT)
**File:** `00_MANDATORY_auto_test_fix_process.mdc`

**Key Requirements:**
- [ ] Read ALL rules in `ai_docs/rules/` before starting
- [ ] Test feature in browser using browser_subagent
- [ ] If issues found → Create rule + Fix + Test again (loop until clean)
- [ ] Only report success when: no build errors, no runtime errors, feature works, visual design matches, all rules followed

---

### 🔧 Component & Import Verification

#### 2. Verify Component Imports
**File:** `verify_component_imports.mdc`

**Mandatory Checklist:**
- [ ] BEFORE importing ANY component, run `list_dir` on the component directory
- [ ] Verify the exact filename exists in the output
- [ ] If missing: Create the component first

#### 3. Verify Component Exports
**File:** `verify_component_exports.mdc`

**Mandatory Checklist:**
- [ ] BEFORE importing from a UI component, view the file to see what it exports
- [ ] Verify the exact export name matches what you're importing
- [ ] If missing: Add the missing export to the component file

---

### 🔐 Authentication & Security

#### 4. Check Auth Dependencies
**File:** `check_auth_dependencies.mdc`

**Mandatory Checklist:**
- [ ] Verify auth token is included in all API requests
- [ ] Use `useAuth` hook to get token
- [ ] Handle 401 responses (token expired)

---

### 🛠️ Build & Error Handling

#### 6. Build Error Logging
**File:** `build_error_logging.mdc`

**Checklist:**
- [ ] If build errors occur, redirect output to log file
- [ ] Read FULL error log file
- [ ] Never trust truncated terminal output

---

### 🎨 UI/UX Consistency

#### 8. Visual Design Consistency
**File:** `visual_design_consistency.mdc`

**Design Tokens:**
- **Backgrounds:** White (#FFFFFF)
- **Text:** Dark headings (#111827), Muted body (#6B7280)
- **Borders:** Subtle (#E5E7EB)
- **Shadows:** Soft, minimal (shadow-sm)
- **Rounded Corners:** 12px+ for cards

**Checklist:**
- [ ] Before creating any new UI element, read `dashboard_visual_description.md`
- [ ] Use specified colors, not arbitrary ones

#### 9. Interactive Elements Must Have Actions
**File:** `interactive_elements_must_have_actions.mdc`

**Rules:**
- [ ] Never create a button without an `onClick` handler
- [ ] Always implement the action when creating the UI element

#### 10. Locale-Aware Routing
**File:** `locale_aware_routing.mdc`

**Rules:**
- [ ] Always use current locale from `useParams()`
- [ ] Always prefix routes with the locale: `/${locale}/dashboard/students`

---

### 📝 Code Quality & Scope

#### 11. Strict Scope Enforcement
**File:** `strict_scope.mdc`

**Rules:**
- [ ] Only implement what's requested in this task
- [ ] Don't refactor unrelated code
- [ ] Don't change existing "Add Student" functionality

---

**🎯 Ready to Implement!**

This task definition provides everything needed to complete the Student Management module. Follow the implementation plan phase by phase, test thoroughly, and deliver a production-ready feature.
