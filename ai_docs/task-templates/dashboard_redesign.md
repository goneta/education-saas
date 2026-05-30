# Task: Dashboard Redesign & Modernization

## 1. Task Overview

### Task Title
**Title:** Dashboard Redesign - Modern Premium UI with Collapsible Sidebar & AI Integration

### Goal Statement
**Goal:** Redesign the application dashboard, preview panel, AI Agent chat area, and sidebar to match the provided premium design references. The objective is to create a "Wow" factor with a visually rich, responsive, and modern interface (Glassmorphism, vibrant colors, smooth animations) while maintaining existing functionality.

---

## 2. Project Analysis & Current State

### Technology & Architecture
- **Frameworks & Versions:** Next.js 14+, TailwindCSS v4, Shadcn/UI
- **Language:** TypeScript
- **UI & Styling:** Vanilla CSS variables in `globals.css` (Tailwind v4 theme), Lucide Icons
- **Key Architectural Patterns:** App Router, Server Components, Client Components for interactivity

### Current State
- Existing `globals.css` defines a "Clean Light" and "Cote d'Ivoire Dark" theme.
- Dashboard layout exists in `app/[locale]/dashboard/layout.tsx`.
- Basic functional structure is in place but lacks the requested "Premium" visual polish.

## 3. Context & Problem Definition

### Problem Statement
The current dashboard design is functional but generic. The user wants a premium, high-end look (based on referenced images) with specific attention to the sidebar (collapsible), preview panel, and AI chat area.

### Success Criteria
- [ ] Dashboard matches the visual style of reference images (Modern, Glassmorphism, Premium).
- [ ] Sidebar is collapsible with a specific visual treatment for the toggle icon.
- [ ] AI Agent chat area is integrated and styled as a premium feature.
- [ ] Preview panel is distinct and well-integrated.
- [ ] Responsive design works across devices.
- [ ] No loss of existing functionality.

---

## 4. Development Mode Context

### Development Mode Context
- **🚨 Project Stage:** Active Development / Refactoring
- **Breaking Changes:** UI breaking changes are expected (redesign), but functional logic must remain.
- **Priority:** High Visual Impact (Aesthetics are critical).

---

## 5. Technical Requirements

### Functional Requirements
- User can toggle the sidebar (expand/collapse) with a smooth animation and custom icon.
- User can view key metrics in redesigned cards.
- User can interact with the AI Agent in a dedicated, styled chat interface.
- System automatically adapts layout for "Preview Panel" visibility.

### Non-Functional Requirements
- **Performance:** Animations must be 60fps (use CSS transforms).
- **Usability:** High contrast text, clear visual hierarchy.
- **Responsive Design:** Mobile-first, sidebar becomes a drawer on small screens.
- **Theme Support:** Must look stunning in both Light and Dark modes.

---

## 6. Data & Database Changes
*No database changes required for this UI task.*

---

## 7. API & Backend Changes
*No backend changes required.*

---

## 8. Frontend Changes

### New Components
- `components/layout/sidebar.tsx`: Redesigned collapsible sidebar.
- `components/dashboard/stat-card.tsx`: Premium styled metric cards.
- `components/dashboard/ai-chat-widget.tsx`: Floating or embedded AI chat interface.
- `components/dashboard/preview-panel.tsx`: dedicated preview area.

### Page Updates
- `app/[locale]/dashboard/layout.tsx`: Update to grid layout to support the new sidebar and preview panel.
- `app/[locale]/dashboard/page.tsx`: Update content usage of new components.
- `globals.css`: Refine color palette and add glassmorphism utilities (backdrop-blur, gradients).

---

## 9. Implementation Plan

### Phase 1: Foundation & Theme
- [ ] Update `globals.css` with new "Premium" tokens (gradients, shadows, glass effects).
- [ ] Create basic layout structure in `dashboard/layout.tsx`.

### Phase 2: Components
- [ ] Build `Sidebar` component (Collapsible logic + Animation).
- [ ] Build `StatCard` and `DashboardGrid`.
- [ ] Build `AiChatWidget` (Visuals only first).
- [ ] Build `PreviewPanel` skeleton.

### Phase 3: Integration & Polish
- [ ] Integrate components into `dashboard/page.tsx`.
- [ ] Verify responsiveness.
- [ ] Add micro-animations (hover states, transitions).

## 10. Task Completion Tracking
- [ ] Theme Updated
- [ ] Sidebar Implemented
- [ ] Chat Widget Implemented
- [ ] Layout Assembled
- [ ] Mobile Verified

---

## 11. File Structure & Organization
- Modify: `app/globals.css`
- Modify: `app/[locale]/dashboard/layout.tsx`
- Create: `components/ui/glass-card.tsx` (Reusable glass container)
- Create: `components/dashboard/*`

---

## 12. AI Agent Instructions

### Implementation Workflow
1.  **Read Rules**: Always check coding standards.
2.  **Style First**: Implement the CSS tokens first to ensure consistency.
3.  **Componentize**: Don't build everything in `page.tsx`. Use small reusable components.
4.  **Verify**: Check mobile view freqently.

### Code Quality Standards
- Use Tailwind classes for everything.
- Avoid inline styles.
- strictly type props.

---
