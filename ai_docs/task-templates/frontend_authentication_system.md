# Task: Frontend Login/Authentication System

## 1. Task Overview

### Task Title
**Title:** Implement Frontend Login/Authentication System

### Goal Statement
**Goal:** Create a complete authentication system in the frontend that allows users to log in, stores JWT tokens securely, and provides authentication state throughout the application. This enables users to access protected features like creating students, managing courses, etc.

---

## 2. Project Analysis & Current State

### Technology & Architecture
- **Frontend Framework:** Next.js 14+ with App Router
- **Language:** TypeScript
- **State Management:** React Context API (to be implemented)
- **Storage:** localStorage for JWT tokens
- **Backend API:** FastAPI with JWT authentication (already implemented)

### Current State
- Backend has complete authentication system:
  - `POST /auth/token` - Login endpoint (returns JWT token)
  - `POST /auth/register/school` - School registration
  - `GET /auth/me` - Get current user info
  - JWT token validation via `security.get_current_user`
- Frontend has NO authentication system:
  - No login page
  - No auth context/state management
  - No token storage mechanism
  - No way for users to authenticate
- Protected features (Add Student) fail with "Not authenticated" error

---

## 3. Context & Problem Definition

### Problem Statement
Users cannot access protected features because there's no way to log in through the frontend. Currently, users must manually obtain JWT tokens via Postman/curl and set them in localStorage, which is not user-friendly or practical for production use.

### Success Criteria
- [ ] Users can log in with email and password
- [ ] JWT token is stored securely in localStorage
- [ ] Authentication state is available throughout the app
- [ ] Protected routes redirect to login if not authenticated
- [ ] Users can log out
- [ ] Token expiration is handled gracefully
- [ ] Login page matches visual design from `dashboard_visual_description.md`

---

## 4. Development Mode Context
- **Project Stage:** Active Development
- **Breaking Changes:** None - this is a new feature
- **Data Handling:** No data migration needed
- **User Base:** School administrators, teachers, students
- **Priority:** High - blocks many other features

---

## 5. Technical Requirements

### Functional Requirements

#### 1. Login Page
- Email input field
- Password input field (masked)
- "Login" button
- Error message display for failed login
- Loading state during authentication
- "Remember me" checkbox (optional)

#### 2. Authentication Context
- Global auth state (user, token, isAuthenticated)
- Login function
- Logout function
- Token refresh mechanism (future enhancement)
- Automatic token validation on app load

#### 3. Token Management
- Store JWT token in localStorage
- Include token in all API requests to protected endpoints
- Clear token on logout
- Handle token expiration (401 responses)

#### 4. Protected Routes
- Redirect to login if not authenticated
- Preserve intended destination (redirect back after login)
- Show loading state while checking auth

#### 5. User Profile Display
- Show logged-in user's name in header
- User dropdown menu with logout option

### Non-Functional Requirements
- **Security:** 
  - Password field must be masked
  - Token stored in localStorage (httpOnly cookies would be better but requires backend changes)
  - Clear token on logout
- **Performance:** Login should complete within 2 seconds
- **Usability:** Clear error messages, intuitive flow
- **Accessibility:** Keyboard navigation, proper labels, ARIA attributes

### Technical Constraints
- Must use existing backend `/auth/token` endpoint
- Must maintain visual design from `dashboard_visual_description.md`
- Must not break existing functionality
- Must work with Next.js App Router

---

## 6. Data & Database Changes
**None** - Backend authentication system already exists.

---

## 7. API / Backend Changes
**None** - Using existing endpoints:
- `POST /auth/token` - Login (returns access_token)
- `GET /auth/me` - Get current user info

---

## 8. Frontend Changes

### New Components to Create

#### 1. `app/[locale]/login/page.tsx`
**Purpose:** Login page
**Features:**
- Email and password form
- Submit to `/auth/token` endpoint
- Store token in localStorage
- Redirect to dashboard on success

#### 2. `contexts/auth-context.tsx`
**Purpose:** Global authentication state
**Features:**
- AuthProvider component
- useAuth hook
- Login/logout functions
- Current user state
- Token management

#### 3. `components/auth/login-form.tsx`
**Purpose:** Reusable login form component
**Features:**
- Form validation
- Error handling
- Loading states
- Visual design matching reference

#### 4. `components/layout/user-menu.tsx`
**Purpose:** User profile dropdown in header
**Features:**
- Display user name
- Logout button
- Profile link (future)

#### 5. `middleware.ts` (optional)
**Purpose:** Protect routes at middleware level
**Features:**
- Check authentication before rendering protected pages
- Redirect to login if not authenticated

### Modified Components

#### `app/[locale]/layout.tsx`
**Changes:**
- Wrap app with AuthProvider
- Make auth context available globally

#### `components/dashboard/header.tsx`
**Changes:**
- Add UserMenu component
- Show user name when logged in

#### `components/students/add-student-modal.tsx`
**Changes:**
- Use auth context to get token instead of localStorage directly
- Remove manual token instructions (no longer needed)

---

## 9. Implementation Plan

### Phase 1: Auth Context & State Management
1. ❌ Create `contexts/auth-context.tsx`
   - Define AuthContext interface
   - Implement AuthProvider
   - Create useAuth hook
   - Add login/logout functions
   - Add token storage/retrieval

### Phase 2: Login Page
2. ❌ Create `app/[locale]/login/page.tsx`
   - Basic page structure
   - Import LoginForm component
3. ❌ Create `components/auth/login-form.tsx`
   - Email and password inputs
   - Form validation
   - Submit handler
   - Error display
   - Loading state
   - Visual styling

### Phase 3: Integration
4. ❌ Update `app/[locale]/layout.tsx`
   - Wrap with AuthProvider
5. ❌ Create `components/layout/user-menu.tsx`
   - User dropdown with logout
6. ❌ Update `components/dashboard/header.tsx`
   - Add UserMenu component
7. ❌ Update `components/students/add-student-modal.tsx`
   - Use useAuth hook instead of localStorage

### Phase 4: Route Protection
8. ❌ Add route protection logic
   - Check auth on dashboard pages
   - Redirect to login if not authenticated
9. ❌ Handle token expiration
   - Catch 401 errors
   - Clear token and redirect to login

### Phase 5: Testing & Polish
10. ❌ Test login flow end-to-end
11. ❌ Test logout functionality
12. ❌ Test protected routes
13. ❌ Test token expiration handling
14. ❌ Verify visual design matches reference

---

## 10. Testing & Verification

### Manual Testing Checklist
- [ ] Navigate to /login → Login page appears
- [ ] Enter invalid credentials → Error message shown
- [ ] Enter valid credentials → Redirected to dashboard
- [ ] User name appears in header
- [ ] Click logout → Token cleared, redirected to login
- [ ] Try to access /dashboard without login → Redirected to login
- [ ] Login → Redirected back to intended page
- [ ] Create student → Works without manual token setup
- [ ] Token expires → Redirected to login with message
- [ ] Test on mobile → Login form is usable

### Edge Cases
- [ ] Network error during login
- [ ] Invalid token format
- [ ] Token expires while using app
- [ ] Multiple tabs (token sync)
- [ ] Browser refresh (token persists)

---

## 11. AI Agent Instructions
- **CRITICAL:** Follow `check_auth_dependencies.mdc` rule
- **CRITICAL:** Follow `verify_component_imports.mdc` rule - check components exist before importing
- **CRITICAL:** Follow `visual_design_consistency.mdc` rule - match `dashboard_visual_description.md`
- **DO NOT** modify backend code
- **DO NOT** change token format or authentication logic
- Use TypeScript for type safety
- Add proper error handling
- Add loading states for better UX

---

## 12. Impact Analysis

### Files to Create
- `contexts/auth-context.tsx`
- `app/[locale]/login/page.tsx`
- `components/auth/login-form.tsx`
- `components/layout/user-menu.tsx`

### Files to Modify
- `app/[locale]/layout.tsx` (wrap with AuthProvider)
- `components/dashboard/header.tsx` (add UserMenu)
- `components/students/add-student-modal.tsx` (use auth context)

### Dependencies to Add
- None (using existing React Context API)

### Breaking Changes
- None - this is a new feature

### Performance Impact
- Minimal - auth check on page load
- Token stored in localStorage (fast access)
- No impact on page load time

---

## 13. Future Enhancements
- Implement "Remember Me" functionality
- Add password reset flow
- Add email verification
- Implement refresh tokens
- Add social login (Google, Microsoft)
- Add two-factor authentication (2FA)
- Move to httpOnly cookies for better security
- Add session timeout warnings
- Add "Keep me logged in" option
- Add login activity log
