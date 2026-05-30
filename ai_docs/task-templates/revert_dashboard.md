# Task: Revert Dashboard to Original State

## 1. Task Overview

### Task Title
**Title:** Revert Dashboard Redesign

### Goal Statement
**Goal:** Completely revert the dashboard layout, design, and components to the state before the "Dark Mode" 3-column implementation. Restore the original clean application state.

---

## 2. Project Analysis & Current State

### Current State
- Dashboard has a 3-column layout (AiPanel, CenterNav, RightPreview).
- Visuals are dark/premium (rejected by user).
- New components exist in `components/dashboard`.

### Desired State
- Original `layout.tsx` and `page.tsx`.
- No `AiPanel`, `CenterNav`, `RightPreview`.

---

## 3. Implementation Plan

### Steps
1.  **Git Restore**: Revert modifications to `dashboard/layout.tsx`, `dashboard/page.tsx`, `globals.css`.
2.  **Git Clean**: Remove new untracked files (`components/dashboard/ai-panel.tsx`, etc.).
3.  **Verification**: Confirm "dark mode" is gone.

---

## 4. AI Agent Instructions
- **Strictly** only revert. Do not "fix" anything else.
