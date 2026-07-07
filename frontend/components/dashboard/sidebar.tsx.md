# sidebar.tsx

## Source File

- `frontend/components/dashboard/sidebar.tsx`

## Purpose

- Owns dashboard navigation, collapsible module groups, and the bottom user account menu.
- Exposes localized account destinations for overview, renewals, security, sessions, contact, payments, credit, invoices, preferences, notifications, team members, and referrals.
- Includes TeducAI Emploi dashboard entries for student CV/sharecode management, recruiter ATS management, and Super Admin employment oversight.

## DOX Scope

- Nearest contract: `frontend/components/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Account labels must use the `account` translation namespace.
- Preserve independent sidebar scrolling and dark-mode readability.
- The active route uses the same dark surface as the hover state and keeps icons/text high contrast.
- Sidebar entries are filtered by account type: recruiters see recruiter workspace links, external students see CV workspace links, school users do not see recruiter-only dashboards, non-student school roles do not see the student Emploi dashboard link, and the Admin Emploi entry is visible only to `super_admin`.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
- Has a dedicated "Smart Transport" section (Tableau de bord, Chauffeurs, Véhicules, Trajets, Affectations); transport was moved here out of Operations.
- #8 Role-based dashboards: Teacher/Student/Parent get curated menus (no admin sections — Gestion, Finances admin, Opérations, Système hidden); all other roles keep the full menu. Establishment selector already scoped server-side via accessible_schools_query (memberships + school_id).
- #7 Payroll: Finance section gains "Paie" (admin `/finance/payroll`); Teacher menu gains a Finance "Mes bulletins" self-service entry (`/finance/my-payslips`).
- #1 UI-less features: Gestion gains Congés (`/hr/leave`) + Annonces (`/communication`); Teacher menu gains Congés (self-service).
- System section gains "API & Integrations" (`/dashboard/extensibility`).
- Security: the quick account-creation form no longer pre-fills a hardcoded default password.
- System section gains "Automatisations" (`/dashboard/automations`).
- Automation B: Student and Parent menus gain "Mes documents" (`/dashboard/my-documents`, FileCheck2) — self-service certificats/attestations/reçus.
- Automation D: Student and Parent menus gain "Planning de revision" (`/dashboard/study-plan`, CalendarCheck).
- Automation D: Teacher menu gains "Remediation IA" (`/dashboard/remediation`, GraduationCap) after Grades.
- Automation D: Student and Parent menus gain "Explique ma note" (`/dashboard/explain-grade`, HelpCircle).
- Automation D: Teacher menu gains "Sequence IA" (`/dashboard/sequence-builder`, BookOpen) after Remediation.
- Automation D: Teacher menu gains "Notes par photo" (`/dashboard/grade-scan`, ScanLine) after Grades.
- Homework module: teacher/admin menus gain "Devoirs" (`/dashboard/assignments`, ClipboardList); student/parent menus gain "Mes devoirs" (`/dashboard/my-assignments`).
- Billing module: Finance menu gains "Billing" (`/dashboard/finance/billing`, WalletCards) right after the Finance root (admin/accountant/director menus).
