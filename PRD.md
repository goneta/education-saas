# Product Requirements Document (PRD) - Educational SaaS

## Goal
Build a complete Educational Institution Management SaaS covering all **26 Functional Modules**. The system will feature an AI Agent foundation and use a modern Python/React stack.

## Tech Stack & Architecture
*   **Frontend**: Next.js 14+ (React), TailwindCSS, Shadcn/UI. PWA support.
*   **Backend**: Python FastAPI (Async).
    *   **AI Engine**: LangChain + OpenAI/Open Source Models (RAG for school documents).
    *   **Task Queue**: Celery/Redis for background jobs (reports, emails).
*   **Database**:
    *   **Development**: SQLite (Local) + MongoDB Atlas (Cloud) to avoid Docker dependency.
    *   **Production**: PostgreSQL + MongoDB.
*   **Infrastructure**: Vercel (Frontend) + Render/Railway (Backend).

## Comprehensive Module Roadmap

### Phase 1: Core Foundation & MVP (Months 1-4)
**Goal**: Launchable product for a single school to manage basics.
*   **Module 11: Administrative Management**: Registration, Student Profiles, Digital Files.
*   **Module 3: Educational Management**: Classes, Subjects, Timetables, Grades, Report Cards.
*   **Module 1: Financial Management (Basic)**: Fee Collection, Receipt Generation, Basic Expense Tracking.
*   **Module 19: Multi-Institution Foundation**: Schema design to support multiple tenants (School Group) from day 1.

### Phase 2: Communication & Operations (Months 5-7)
**Goal**: Enhance engagement and internal operations.
*   **Module 2: Messaging & Communication**: SMS/Email gateways, In-app chat, Notifications (Grades, Delays).
*   **Module 12: HR Management**: Staff profiles, Contracts, Leave/Absence management, Payroll.
*   **Module 13: Infrastructure & Building**: Classroom booking, Maintenance requests.
*   **Module 22: Payment Integration**: Stripe, Mobile Money (Orange, MTN, Moov, Wave).
*   **Module 24: Shared Document Space**: Secure file upload/sharing with permissions.

### Phase 3: Advanced Features & AI (Months 8-10)
**Goal**: Differentiate with AI and logistics handling.
*   **Module 23: AI Agent Integration**:
    *   **Student AI**: Homework helper, Personalized resources.
    *   **Teacher AI**: Auto-lesson plans, Grading assistant.
    *   **Admin AI**: "Generate financial report for Q1" (Natural Language-to-SQL).
*   **Module 4: Cafeteria**: Ticket management, POS system.
*   **Module 8: Transportation**: Bus fleet, Route planning, Geo-tracking.
*   **Module 14: Library**: Book inventory, Loans, Late fees.
*   **Module 25: Electronic Signature**: Legally binding digital signatures for contracts/reports.
*   **Module 26: QR Codes**: Student ID cards, Access control, Event entry.

### Phase 4: Expansion & Ecosystem (Months 11-13)
**Goal**: National scale and 3rd party integration.
*   **Module 20: Ministry Access**: National/Regional reporting dashboards.
*   **Module 21: Public API**: Webhooks, Developer documentation.
*   **Module 18: Advanced Reporting**: BI Dashboards, Predictive Analytics.
*   **Module 5, 6, 7**: IT Inventory, CCTV Management, Parking Management.
*   **Module 9, 10, 15, 16, 17**: Extracurriculars, Partners, Health, Discipline, Official Exams.

## Global & African Multilanguage System
**Requirement**: Support Major Global languages + African languages (Written/Spoken/Tribal).
*   **Strategy**: `next-intl` (Frontend) + `ReferenceData` (Backend).

## Dynamic Education Levels (Francophone Africa Focus)
**Requirement**: Nursery to University, flexible/editable by Admin.
*   **Maternelle**: Petite/Moyenne/Grande Section.
*   **Primaire**: CP, CE1, CE2, CM1, CM2.
*   **Secondaire**: 6ème, 5ème, 4ème, 3ème.
*   **Lycée**: 2nde, 1ère, Terminale.
*   **Supérieur**: Licence (L1-L3), Master (M1-M2), Doctorat.
