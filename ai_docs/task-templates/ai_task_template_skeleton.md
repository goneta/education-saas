# AI Task Planning Template - Starter Framework

> **About This Template:** This is a systematic framework for planning and executing technical projects with AI assistance. Use this structure to break down complex features, improvements, or fixes into manageable, trackable tasks that AI agents can execute effectively.

---

## 1. Task Overview

### Task Title
<!-- Give your task a clear, specific name that describes what you're building or fixing -->
**Title:** [Brief, descriptive title - e.g., "Add User Authentication System" or "Fix Payment Integration Bug"]

### Goal Statement
<!-- Write one paragraph explaining what you want to achieve and why it matters for your project -->
**Goal:** [Clear statement of the end result you want and the business/user value it provides]

---

## 2. Project Analysis & Current State

### Technology & Architecture
<!-- This is where you document your current tech stack so the AI understands your environment -->
- **Frameworks & Versions:** TODO: List your main frameworks and versions
- **Language:** TODO: Specify your programming language and version
- **Database & ORM:** TODO: Define your database and ORM choice
- **UI & Styling:** TODO: List your UI framework and styling approach
- **Authentication:** TODO: Specify your authentication system
- **Key Architectural Patterns:** TODO: List your main architectural patterns

### Current State
<!-- Describe what exists today - what's working, what's broken, what's missing -->
[Analysis of your current codebase state, existing functionality, and what needs to be changed]

## 3. Context & Problem Definition

### Problem Statement
<!-- This is where you clearly define the specific problem you're solving -->
[Detailed explanation of the problem, including user impact, pain points, and why it needs to be solved now]

### Success Criteria
<!-- Define exactly how you'll know when this task is complete and successful -->
- [ ] [Specific, measurable outcome 1]
- [ ] [Specific, measurable outcome 2]
- [ ] [Specific, measurable outcome 3]

---

## 4. Development Mode Context

### Development Mode Context
<!-- This is where you tell the AI agent about your project's constraints and priorities -->
- **🚨 Project Stage:** TODO: Define if this is new development, production system, or legacy migration
- **Breaking Changes:** TODO: Specify if breaking changes are acceptable or must be avoided
- **Data Handling:** TODO: Define data preservation requirements
- **User Base:** TODO: Describe who will be affected by changes
- **Priority:** TODO: Set your speed vs stability priorities

---

## 5. Technical Requirements

### Functional Requirements
<!-- This is where the AI will understand exactly what the system should do - be specific about user actions and system behaviors -->

TODO: Define what users can do and what the system will automatically handle
- Example format: "User can [specific action]"
- Example format: "System automatically [specific behavior]" 
- Example format: "When [condition] occurs, then [system response]"

### Non-Functional Requirements
<!-- This is where you define performance, security, and usability standards -->
- **Performance:** TODO: Define response time and load handling requirements
- **Security:** TODO: Specify authentication and data protection needs
- **Usability:** TODO: Set user experience and accessibility standards
- **Responsive Design:** TODO: Define mobile, tablet, desktop support requirements
- **Theme Support:** TODO: Specify light/dark mode and brand requirements

### Technical Constraints
<!-- This is where you list limitations the AI agent must work within -->
- [Must use existing system X]
- [Cannot modify database table Y]
- [Must maintain compatibility with feature Z]

---

## 6. Data & Database Changes

### Database Schema Changes
<!-- This is where you specify any database modifications needed -->

TODO: Add your SQL schema changes here (new tables, columns, indexes, etc.)

### Data Model Updates
<!-- This is where you define TypeScript types, schema updates, or data structure changes -->

TODO: Define your TypeScript types, interfaces, and data structure changes

### Data Migration Plan
<!-- This is where you plan how to handle existing data during changes -->

TODO: Plan your data migration steps (backup, apply changes, transform data, validate)

---

## 7. API & Backend Changes

### Data Access Pattern Rules
<!-- This is where you tell the AI agent how to structure backend code in your project -->

TODO: Define where different types of code should go in your project (mutations, queries, API routes)

### Server Actions
<!-- List the backend mutation operations you need -->

TODO: List your create, update, delete operations and what they do

### Database Queries
<!-- Specify how you'll fetch data -->

TODO: Define your data fetching approach (direct queries vs separate functions)

---

## 8. Frontend Changes

### New Components
<!-- This is where you specify UI components to be created -->

TODO: List the new components you need to create and their purpose

### Page Updates
<!-- This is where you list pages that need modifications -->

TODO: List the pages that need changes and what modifications are required

### State Management
<!-- This is where you plan how data flows through your frontend -->

TODO: Define your state management approach and data flow strategy

---

## 9. Implementation Plan

TODO: Break your work into phases with specific tasks and file paths

---

## 10. Task Completion Tracking

### Real-Time Progress Tracking
<!-- This is where you tell the AI agent to update progress as work is completed -->

TODO: Define how you want the AI to track and report progress on tasks

---

## 11. File Structure & Organization

TODO: Plan what new files to create and existing files to modify

---

## 12. AI Agent Instructions

### Implementation Workflow
<!-- This is where you give specific instructions to your AI agent -->
🎯 **MANDATORY PROCESS:**

**Rule Management:**
- When you create a new rule in `ai_docs/rules/`, you MUST immediately update this template file (`ai_task_template_skeleton.md`) to include that rule in section 14
- This ensures all future tasks benefit from lessons learned

**Task Creation:**
- When creating a new task, you MUST use `ai_task_template_skeleton.md` as the base template
- This ensures every task includes all current rules and best practices

**Task Execution:**
- When implementing a feature, you MUST use the created task file as the source of truth
- Follow all rules and checklists defined in the task
- Update task progress as you work

TODO: Add any additional project-specific workflow requirements

### Communication Preferences
<!-- This is where you set expectations for how the AI should communicate -->
TODO: How do you want the agent to communicate with you

### Code Quality Standards
<!-- This is where you define your coding standards for the AI to follow -->
TODO: Any specific code standards

---

## 13. Second-Order Impact Analysis

### Impact Assessment
<!-- This is where you think through broader consequences of your changes -->

TODO: Tell the AI what sections of code you're worried about breaking, performance concerns, and user workflow impacts

---

## 14. Mandatory Rules & Best Practices

> **📋 CRITICAL:** These rules represent lessons learned from past errors. Follow ALL rules during implementation.
> 
> Full rule details are in `ai_docs/rules/` - read the complete files for comprehensive guidance.

### 🚨 Critical Process Rules

#### 1. Auto-Test-Fix Process (MOST IMPORTANT)
**File:** `00_MANDATORY_auto_test_fix_process.mdc`

**Summary:** MANDATORY process for every task - auto-check, auto-test, auto-fix, and auto-create rules.

**Key Requirements:**
- [ ] Read ALL rules in `ai_docs/rules/` before starting
- [ ] Test feature in browser using browser_subagent
- [ ] If issues found → Create rule + Fix + Test again (loop until clean)
- [ ] Only report success when: no build errors, no runtime errors, feature works, visual design matches, all rules followed
- [ ] Create rules proactively for any new error patterns

**Remember:** You are responsible for quality, not the user. Test everything before reporting success.

---

### 🚨 Continuous Improvement

#### 2. Auto-Create Rule on Error (MANDATORY)
**File:** `01_MANDATORY_auto_create_rule_on_error.mdc`

**Summary:** Whenever an "error", "issue", or "mistake" occurs, you MUST automatically create a new rule and update this template.

**Trigger Signals:**
- Words: "error", "issue", "mistake"
- Events: Build failure, Runtime crash, User rejection, UI bug

**Mandatory Checklist:**
- [ ] Identify the root cause of the error/issue
- [ ] Create a new rule in `ai_docs/rules/` to prevent recurrence
- [ ] Update `ai_task_template_skeleton.md` to include the new rule
- [ ] Verify the fix works AND the process is updated

#### 3. Fix Missing Components on Build Error (MANDATORY)
**File:** `02_MANDATORY_fix_missing_components.mdc`

**Summary:** When "Module not found" occurs for `components/ui`, you MUST create the component immediately.

**Trigger Signals:**
- Build Error: "Module not found"
- Path: `components/ui/*` or shared components

**Mandatory Checklist:**
- [ ] Read build log to identify missing file
- [ ] Check if file exists using `list_dir`
- [ ] Install dependency (if shadcn) or create file
- [ ] Retry build

#### 4. Always Clean Build (MANDATORY)
**File:** `03_MANDATORY_always_clean_build.mdc`

**Summary:** Debugging build errors? Clean `.next` first.

**Validation:**
- [ ] `Remove-Item -Recurse -Force .next` executed?

---

#### 5. Missing Dependency Check (MANDATORY)
**File:** `check_dependencies.mdc`

**Summary:** Determine root cause of "Module not found" - often missing package install.

**Trigger Signals:**
- Build Error: "Module not found: Can't resolve..." (especially `@radix-ui/...`)

**Mandatory Checklist:**
- [ ] Check import path in error.
- [ ] If `@radix-ui/...` or external lib -> Run `npm install <package>`.
- [ ] If local file -> Check file existence.
- [ ] Don't just modify code; fix the environment first.

---

### 🔧 Component & Import Verification

#### 2. Verify Component Imports
**File:** `verify_component_imports.mdc`

**Summary:** Prevent "Module not found" errors by verifying component existence before import.

**Mandatory Checklist:**
- [ ] BEFORE importing ANY component, run `list_dir` on the component directory
- [ ] Verify the exact filename exists in the output
- [ ] If missing: Create the component first
- [ ] NO EXCEPTIONS - even if you "created" it earlier, verify it exists

#### 3. Verify Component Exports
**File:** `verify_component_exports.mdc`

**Summary:** Prevent "Export doesn't exist" errors by checking exports match imports.

**Mandatory Checklist:**
- [ ] BEFORE importing from a UI component, view the file to see what it exports
- [ ] Verify the exact export name matches what you're importing
- [ ] If missing: Add the missing export to the component file
- [ ] Never assume a component exports something just because it's a standard pattern

---

### 🔐 Authentication & Security

#### 4. Check Auth Dependencies
**File:** `check_auth_dependencies.mdc`

**Summary:** Verify authentication system exists before implementing features that require protected API endpoints.

**Mandatory Checklist:**
- [ ] Check if login page/component exists in frontend
- [ ] Check if auth context/state management exists
- [ ] Check if token storage mechanism is implemented
- [ ] If any are missing: Create task for authentication first OR provide workaround

**Remember:** Backend auth ≠ Frontend auth. Always verify both.

#### 5. Create Test Users for Auth
**File:** `create_test_users_for_auth.mdc`

**Summary:** Always create test users with simple credentials when implementing login/authentication systems.

**Mandatory Checklist:**
- [ ] Create test user creation script
- [ ] Run script to create test user with simple credentials (e.g., admin@test.com / admin123)
- [ ] Test login with these credentials
- [ ] Verify login works end-to-end
- [ ] Provide credentials to user in clear format
- [ ] Document in walkthrough or README

---

### 🛠️ Build & Error Handling

#### 6. Build Error Logging
**File:** `build_error_logging.mdc`

**Summary:** Implement proper build error logging to capture full error messages for debugging.

**Mandatory Workflow:**
```powershell
# Step 1: Clean build
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue

# Step 2: Build with full logging
npm run build > build.log 2>&1

# Step 3: Read full error log
Get-Content build.log
```

**Checklist:**
- [ ] Clean `.next` directory before rebuilding
- [ ] Run build with output redirect to file
- [ ] Read FULL error log file
- [ ] Never trust truncated terminal output

#### 7. TypeScript Config Errors
**File:** `typescript_config_errors.mdc`

**Summary:** Prevent TypeScript errors in configuration files by understanding return type requirements.

**Key Points:**
- [ ] Read TypeScript error messages completely
- [ ] Check what type is expected vs what you're providing
- [ ] Look for "missing property" errors - add the property
- [ ] Use type assertions (`as Type`) when you know the type is correct
- [ ] Test with `npx tsc --noEmit` to see all TypeScript errors
363: 
364: #### 8. Handle Build Log Encoding
365: **File:** `handle_build_log_encoding.mdc`
366: 

#### 8. Handle Build Log Encoding
**File:** `handle_build_log_encoding.mdc`

**Summary:** Handle encoding issues when reading build logs on Windows (e.g. from `npm run build`).

**Checklist:**
- [ ] If `read_file` or `Get-Content` fails with encoding errors, immediately try `cmd /c type`.
- [ ] Do not assume the file is empty or corrupt; it is likely just an encoding mismatch.
- [ ] Trust the "Using type command to read it" fallback if provided by the environment.

#### 9. React Day Picker v9 Migration
**File:** `react_day_picker_v9_migration.mdc`

**Summary:** `react-day-picker` v9 removed `IconLeft`/`IconRight`. Do not use them.

**Checklist:**
- [ ] Remove `components={{ IconLeft: ... }}` from `Calendar` components.
- [ ] Verify build references to `CustomComponents`.

#### 10. Zod & React Hook Form Numbers
**File:** `zod_hook_form_numbers.mdc`

**Summary:** Use `valueAsNumber: true` and `z.number()` for strict numeric inputs to avoid Zod/Resolver type mismatches.

**Checklist:**
- [ ] Use `type="number"` with `{ valueAsNumber: true }` in `register`.
- [ ] Use `z.number()` instead of `z.coerce.number()` where possible for cleaner types.

#### 11. Mandatory DB Schema Update
**File:** `update_db_schema.mdc`

**Summary:** Internal Server Error (500) often means missing tables. Always update DB when adding models.

**Checklist:**
- [ ] Added new model?
- [ ] Ran `python -m backend.init_db`?
- [ ] Verified endpoint response is not 500?

#### 12. Prevent Duplicate Router Modules
**File:** `prevent_duplicate_routers.mdc`

**Summary:** Prevent duplicate router modules by checking existing files.

**Checklist:**
- [ ] `list_dir backend/routers` before implementing.
- [ ] Ensure no duplicate files for the same domain (e.g., `expenses.py` vs `finance.py`).
- [ ] Clean up `main.py` imports/includes if deleting files.

#### 13. Mandatory Verification Before Success
**File:** `verify_before_success.mdc`

**Summary:** NEVER report "Fixed" without proof. Run a script or browser test to verify.

**Checklist:**
- [ ] Applied fix?
- [ ] Ran verification (script, curl, browser)?
- [ ] Verified result is POSITIVE?


---

### 🎨 UI/UX Consistency

#### 8. Visual Design Consistency
**File:** `visual_design_consistency.mdc`

**Summary:** Enforce consistent visual design for all new UI elements based on dashboard_visual_description.md.

**Design Tokens:**
- **Backgrounds:** Light grey (#F7F8FA, #F6F7F9), White (#FFFFFF)
- **Text:** Dark headings (#111827), Muted body (#6B7280), Links (#2563EB)
- **Borders:** Subtle (#E5E7EB)
- **Shadows:** Soft, minimal (shadow-sm)
- **Rounded Corners:** 12px+ for cards
- **Font:** Modern sans-serif (Inter / SF Pro style)

**Checklist:**
- [ ] Before creating any new UI element, read `dashboard_visual_description.md`
- [ ] Use specified colors, not arbitrary ones
- [ ] Ensure clean, minimal SaaS aesthetic

#### 9. Interactive Elements Must Have Actions
**File:** `interactive_elements_must_have_actions.mdc`

**Summary:** Ensure all interactive UI elements have proper event handlers or actions.

**Rules:**
- [ ] Never create a button without an `onClick` handler (unless it's a submit button in a form)
- [ ] Never create a link without a valid `href`
- [ ] Always implement the action when creating the UI element
- [ ] If action is complex: Create placeholder handler with TODO comment

**Remember:** If it looks clickable, it should BE clickable.

#### 10. Locale-Aware Routing
**File:** `locale_aware_routing.mdc`

**Summary:** Ensure proper locale-aware routing in Next.js apps with [locale] dynamic segments.

**Rules:**
- [ ] Never hardcode routes like `/dashboard/students` in apps with `[locale]` segments
- [ ] Always use current locale from `useParams()` or similar hooks
- [ ] Always prefix routes with the locale: `/${locale}/dashboard/students`
- [ ] Test the route in browser before declaring success

---

### 📝 Code Quality & Scope

#### 11. Strict Scope Enforcement
**File:** `strict_scope.mdc`

**Summary:** Enforce strict adherence to user-requested scope, preventing unauthorized changes.

**Rules:**
- [ ] Never change layout, colors, behavior, or functionality unless strictly necessary for the requested task
- [ ] Never "modernize" or "cleanup" code that is not part of the active task
- [ ] Always ask for clarification if a request implies changes that might affect unrelated parts
- [ ] Fix the specific problem, do not re-architect the solution

---

### 💻 Code Integrity & Logic

#### 13. Prevent Duplicate Object Keys
**File:** `prevent_duplicate_object_keys.mdc`

**Summary:** Ensure object literals do not contain duplicate property names to avoid TypeScript errors and runtime bugs.

**Mandatory Checklist:**
- [ ] **Review Before Saving:** Scan object literals for duplicate keys before applying edits.
- [ ] **Lint Check:** Watch for "An object literal cannot have multiple properties with the same name" errors.
- [ ] **Fix immediately:** Remove duplicate keys upon detection.

#### 14. Verify UI Elements Exist Before Logic
**File:** `verify_ui_elements_exist.mdc`

**Summary:** Ensure UI elements exist in JSX before writing logic or payloads that rely on them.

**Mandatory Checklist:**
- [ ] **UI-First:** Add the UI component (Input/Select) *before* or *simultaneously* with state logic.
- [ ] **Visual Verification:** check render method to ensure every form state variable has an input.
- [ ] **Integration Check:** Ensure data-fetching hooks have a corresponding UI element to populate.

### 🔄 Git Operations

#### 12. Preserve Features During Reverts
**File:** `preserve_features_during_reverts.mdc`

**Summary:** Prevent accidental deletion of existing features during git revert operations.

**Rules:**
- [ ] Never use `git clean -fd` without first checking what files will be deleted
- [ ] Always use `git clean -fd --dry-run` first to preview deletions
- [ ] Never assume all untracked files are safe to delete
- [ ] Check if untracked files contain user features from previous sessions
- [ ] Use selective `git restore` on specific files instead of blanket operations

### 🏗️ Component Architecture

#### 15. Verify Modal Imports and Build (MANDATORY)
**File:** `verify_modal_imports_and_build.mdc`

**Summary:** Prevent import errors when using Modals and enforce build verification.

**Mandatory Checklist:**
- [ ] **Check Exports**: Verify if modal uses `export default` or named export and match import exactly.
- [ ] **Check "use client"**: Ensure interactive modals have `"use client"` directive.
- [ ] **Path Verification**: Confirm file exists at path before importing.
- [ ] **Immediate Build Check**: Run `npm run build` immediately after adding a modal.

### 🌐 Server & Browser Testing

#### 16. Check Dev Server Status (MANDATORY)
**File:** `check_dev_server_status.mdc`

**Summary:** Ensure development server is running and accessible before browser testing.

**Mandatory Checklist:**
- [ ] **Verify Port**: Run `Test-NetConnection -ComputerName localhost -Port 3000` before `browser_subagent`.
- [ ] **Analyze Output**: Only proceed if `TcpTestSucceeded` is `True`.
- [ ] **Fix**: If False, run `npm run dev` and wait.
- [ ] **No Curl**: Use PowerShell native `Test-NetConnection`, not `curl`.

---

**🎯 Ready to Plan Your Next Project?**

This template gives you the framework - now fill it out with your specific project details! 

*Want the complete version with detailed examples, advanced strategies, and full AI agent workflows? [Watch the full tutorial video here]*

---

*This template is part of ShipKit - AI-powered development workflows and templates*  
*Get the complete toolkit at: https://shipkit.ai* 
