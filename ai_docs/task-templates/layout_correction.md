# Task: Dashboard Layout Correction (Strict)

## 1. Task Overview

### Task Title
**Title:** Dashboard Layout - 3 Column Structure (AI | Menu | Preview)

### Goal Statement
**Goal:** Implement a specific 3-column layout where the AI Chat Widget is on the Left, the Sidebar (Navigation) is in the Middle, and the Preview Panel is on the Right. Visual style must match references exactly. NO functionality changes.

---

## 2. Project Analysis & Current State

### Technology & Architecture
- Next.js 14+, TailwindCSS, Shadcn/UI

### Current State
- Reverted to original state.

## 3. Context & Problem Definition

### Layout Requirement
**Strict Column Layout:**
1.  **Left Column**: AI Agent Chat (Collapsible toggle here).
2.  **Middle Column**: Dashboard Sidebar / Navigation.
3.  **Right Column**: Preview Section.

### Success Criteria
- [ ] Layout matches strictly: Left(AI) - Center(Menu) - Right(Preview).
- [ ] Colors and visuals match reference images (Dark/Glass).
- [ ] Existing functional logic remains untouched.

---

## 4. Development Mode Context
- **🚨 Project Stage:** Correction / Strict Implementation
- **Priorities:** Accuracy to Layout > Modernization.

---

## 5. Technical Requirements

### Functional Requirements
- AI Chat area is the first section (Left).
- Sidebar is the second section (Center).
- Preview is the third section (Right).
- Collapsing icon is at the top of the AI Chat area.

### Non-Functional Requirements
- **Responsive:** Layout stacks on mobile.

---

## 6. Frontend Changes

### New Components (Visual Only)
- `components/layout/three-column-layout.tsx`: Grid container.
- `components/dashboard/ai-panel.tsx`: Left column.
- `components/dashboard/center-nav.tsx`: Middle column.
- `components/dashboard/right-preview.tsx`: Right column.

### Page Updates
- `app/[locale]/dashboard/layout.tsx`: Implement the 3-column grid.

---

## 7. Implementation Plan
1.  **Layout**: Create the main grid shell.
2.  **Components**: specific containers for the 3 columns.
3.  **Style**: Apply local styles only to these containers to match reference (dark backgrounds, specific borders).

## 8. AI Agent Instructions
- **STRICT RULE**: Do NOT change global theme. Do NOT refactor existing components unless they break the layout.
- **Visuals**: Use dark slate/blue tones as seen in "Dashboard_design1.png".
