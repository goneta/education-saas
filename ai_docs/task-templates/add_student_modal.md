# Task: Add Student Modal/Form

## 1. Task Overview

### Task Title
**Title:** Implement Add Student Modal/Form with Backend Integration

### Goal Statement
**Goal:** Create a modal dialog with a comprehensive form that allows school administrators to register new students. The form will collect all required student information (personal details, parent/guardian information, address) and submit it to the existing backend API endpoint (`POST /students/`). This completes the basic CRUD functionality for student management.

---

## 2. Project Analysis & Current State

### Technology & Architecture
- **Frontend Framework:** Next.js 14+ with App Router
- **Language:** TypeScript
- **UI Components:** Shadcn/UI (Button, Card already available)
- **Styling:** TailwindCSS
- **State Management:** React useState hooks
- **Backend API:** FastAPI (Python)
- **Authentication:** JWT-based (already implemented)

### Current State
- Students page exists at `app/[locale]/dashboard/students/page.tsx`
- "Add Student" button exists with placeholder onClick handler (shows alert)
- Backend API endpoint `POST /students/` is fully implemented and tested
- Required UI components: Button ✅, Card ✅, Input ❌ (need to verify/create), Dialog ❌ (need to create)
- No form validation library integrated yet

---

## 3. Context & Problem Definition

### Problem Statement
School administrators need a way to register new students in the system. Currently, the "Add Student" button shows a placeholder alert. Administrators need a proper form to:
- Enter student personal information (name, email, registration number, date of birth, gender, address)
- Enter parent/guardian information (name, phone, email, address)
- Assign student to a class
- Submit data to the backend API
- See success/error feedback

### Success Criteria
- [ ] Clicking "Add Student" button opens a modal dialog
- [ ] Modal contains a form with all required fields matching backend schema
- [ ] Form has proper validation (required fields, email format, etc.)
- [ ] Form submits data to `POST /students/` endpoint
- [ ] Success: Modal closes, table refreshes, success message shown
- [ ] Error: Error message displayed, form stays open
- [ ] Modal can be closed without submitting (Cancel button or X)
- [ ] Visual design matches `dashboard_visual_description.md`

---

## 4. Development Mode Context
- **Project Stage:** Active Development
- **Breaking Changes:** None - this is a new feature
- **Data Handling:** New student records will be created in database
- **User Base:** School administrators only (role-based access already handled by backend)
- **Priority:** User Experience > Speed (proper validation and feedback are critical)

---

## 5. Technical Requirements

### Functional Requirements
1. **Modal Dialog:**
   - Opens when "Add Student" button is clicked
   - Can be closed via Cancel button, X button, or ESC key
   - Prevents interaction with background content
   - Closes automatically on successful submission

2. **Form Fields (matching backend `StudentCreateSchema`):**
   - **Student Information:**
     - Full Name (text, required)
     - Email (email, required, unique)
     - Password (password, required, min 8 characters)
     - Registration Number/Matricule (text, required, unique)
     - Date of Birth (date, required)
     - Gender (select: Male/Female/Other, required)
     - Student Address (textarea, required)
   
   - **Parent/Guardian Information:**
     - Parent Name (text, required)
     - Parent Phone (tel, required)
     - Parent Email (email, optional)
     - Parent Address (textarea, required)
   
   - **Class Assignment:**
     - Current Class (select dropdown, optional for now - can be assigned later)

3. **Form Validation:**
   - All required fields must be filled
   - Email must be valid format
   - Password must be at least 8 characters
   - Registration number must be unique (backend will validate)
   - Date of birth must be a valid past date

4. **API Integration:**
   - Submit form data to `POST http://localhost:8000/students/`
   - Include JWT token in Authorization header
   - Handle loading state during submission
   - Handle success response (201 Created)
   - Handle error responses (400, 403, 500)

5. **User Feedback:**
   - Show loading spinner during submission
   - Show success message on successful creation
   - Show error message on failure (with specific error from backend)
   - Disable submit button during submission

### Non-Functional Requirements
- **Performance:** Form should be responsive, submission under 2 seconds
- **Security:** Password field should be masked, JWT token required
- **Usability:** Clear labels, helpful error messages, logical field grouping
- **Accessibility:** Proper labels, keyboard navigation, ARIA attributes
- **Responsive Design:** Modal should work on mobile, tablet, desktop

### Technical Constraints
- Must use existing backend API endpoint (no backend changes)
- Must maintain visual design from `dashboard_visual_description.md`
- Must not break existing students page functionality
- Must verify UI components exist before using (follow `verify_component_imports.mdc` rule)

---

## 6. Data & Database Changes
**None** - Backend database schema and API already exist and are tested.

---

## 7. API / Backend Changes
**None** - Using existing `POST /students/` endpoint.

**Existing API Endpoint:**
```
POST /students/
Authorization: Bearer {jwt_token}
Content-Type: application/json

Request Body:
{
  "email": "string",
  "password": "string",
  "full_name": "string",
  "profile": {
    "registration_number": "string",
    "date_of_birth": "YYYY-MM-DD",
    "gender": "Male" | "Female" | "Other",
    "student_address": "string",
    "parent_name": "string",
    "parent_phone": "string",
    "parent_email": "string" (optional),
    "parent_address": "string",
    "current_class_id": number (optional)
  }
}

Response (201):
{
  "id": number,
  "email": "string",
  "full_name": "string",
  "role": "STUDENT",
  "school_id": number,
  "is_active": boolean,
  "student_profile": { ... }
}
```

---

## 8. Frontend Changes

### New Components to Create

#### 1. `components/ui/dialog.tsx`
**Purpose:** Reusable modal dialog component (Shadcn/UI style)
**Status:** ❌ Need to create
**Dependencies:** None

#### 2. `components/ui/input.tsx`
**Purpose:** Reusable input component (Shadcn/UI style)
**Status:** ✅ Already created (verify it exists)

#### 3. `components/ui/label.tsx`
**Purpose:** Form label component
**Status:** ❌ Need to create

#### 4. `components/ui/select.tsx`
**Purpose:** Dropdown select component
**Status:** ❌ Need to create

#### 5. `components/ui/textarea.tsx`
**Purpose:** Multi-line text input
**Status:** ❌ Need to create

#### 6. `components/students/add-student-modal.tsx`
**Purpose:** Main modal component with form
**Status:** ❌ Need to create
**Features:**
- Modal dialog wrapper
- Form with all required fields
- Form validation
- API integration
- Loading states
- Error handling

### Modified Components

#### `app/[locale]/dashboard/students/page.tsx`
**Changes:**
- Add state for modal visibility: `const [showAddModal, setShowAddModal] = useState(false)`
- Replace alert in "Add Student" button onClick with: `setShowAddModal(true)`
- Import and render `<AddStudentModal>` component
- Add callback to refresh student list after successful submission

---

## 9. Implementation Plan

### Phase 1: UI Components Setup
1. ✅ Verify `components/ui/input.tsx` exists (already created)
2. ❌ Create `components/ui/dialog.tsx` (modal wrapper)
3. ❌ Create `components/ui/label.tsx` (form labels)
4. ❌ Create `components/ui/select.tsx` (dropdowns)
5. ❌ Create `components/ui/textarea.tsx` (multi-line input)

### Phase 2: Form Component
6. ❌ Create `components/students/add-student-modal.tsx`
   - Set up form state for all fields
   - Implement form layout with sections (Student Info, Parent Info, Class)
   - Add form validation logic
   - Style according to `dashboard_visual_description.md`

### Phase 3: API Integration
7. ❌ Implement form submission handler
   - Get JWT token from auth context/storage
   - Make POST request to `/students/` endpoint
   - Handle loading state
   - Handle success/error responses

### Phase 4: Integration
8. ❌ Update students page to use modal
   - Add modal state
   - Update "Add Student" button onClick
   - Add callback to refresh student list
   - Test end-to-end flow

### Phase 5: Testing & Polish
9. ❌ Test all form validations
10. ❌ Test API integration (success and error cases)
11. ❌ Test modal open/close behavior
12. ❌ Verify visual design matches reference
13. ❌ Test on mobile/tablet/desktop

---

## 10. Testing & Verification

### Manual Testing Checklist
- [ ] Click "Add Student" → Modal opens
- [ ] Click Cancel → Modal closes without submitting
- [ ] Click X button → Modal closes
- [ ] Press ESC → Modal closes
- [ ] Submit empty form → Validation errors shown
- [ ] Submit with invalid email → Email validation error shown
- [ ] Submit with short password → Password validation error shown
- [ ] Submit valid form → Success, modal closes, student appears in table
- [ ] Submit duplicate email → Backend error shown
- [ ] Submit duplicate registration number → Backend error shown
- [ ] Test on mobile → Form is usable
- [ ] Test keyboard navigation → All fields accessible

### Edge Cases
- [ ] Network error during submission
- [ ] Unauthorized user (401 error)
- [ ] Server error (500 error)
- [ ] Very long names/addresses
- [ ] Special characters in fields

---

## 11. AI Agent Instructions
- **CRITICAL:** Follow `verify_component_imports.mdc` rule - check if UI components exist before importing
- **CRITICAL:** Follow `interactive_elements_must_have_actions.mdc` rule - all buttons must have onClick handlers
- **CRITICAL:** Follow `visual_design_consistency.mdc` rule - match `dashboard_visual_description.md` styling
- **DO NOT** modify backend code
- **DO NOT** change existing students page functionality (except adding modal)
- **DO NOT** break existing visual design
- Use TypeScript for type safety
- Add proper error handling for all API calls
- Add loading states for better UX

---

## 12. Impact Analysis

### Files to Create
- `components/ui/dialog.tsx`
- `components/ui/label.tsx`
- `components/ui/select.tsx`
- `components/ui/textarea.tsx`
- `components/students/add-student-modal.tsx`

### Files to Modify
- `app/[locale]/dashboard/students/page.tsx` (add modal state and integration)

### Dependencies to Add
- None (using existing React, Next.js, fetch API)

### Breaking Changes
- None

### Performance Impact
- Minimal - modal only loads when opened
- API call only on form submission
- No impact on page load time

---

## 13. Future Enhancements
- Add photo upload for student profile
- Add document upload (birth certificate, etc.)
- Add bulk student import (CSV/Excel)
- Add student ID card generation
- Add email notification to parent on registration
- Add class selection with real data from backend
- Add form auto-save (draft)
- Add multi-step wizard for better UX
