# schemas.py

## Source File

- `backend/schemas.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities.
- Exposes API schemas for schools, users, AI billing, and other modules, including username, system-account flags, account type, and dashboard destination hints in user responses.
- Defines Pydantic API contracts for school settings, cash fee payments, AI providers, wallets, targeted credit packs, manual cash/free credit validation, school allocations, platform payments, and school payments.
- AI provider contracts include account labels and available provider credits; platform monitoring contracts expose provider totals, sold/allocated credits, remaining platform credits, wallet balances, threshold settings, and low-credit alert state.
- AI credit purchase contracts carry target context, provider, optional Mobile Money network, redirect URLs, manual-validation notes, checkout URL, and provider status.
- Employment job offer responses expose optional recruiter/company logo URLs returned by the employment router.
- Defines persistent subscription-change/response contracts and exposes managed-user phone/deletion state.
- User, student, and teacher responses expose the optional protected profile-photo endpoint.
- Context contracts cover active assignment/year changes, school-model activation, non-destructive deactivation, AI enablement, and model-level limits.
- Organization owners can create additional schools with a selected set of model codes.
- TeducAI Emploi contracts cover student CV updates, detailed skills, academic credentials, certificates, work history technologies, sharecode lookup, external student registration, recruiter registration, recruiter profile/subscription/AI-credit updates, advanced job offers, applications with AI match scores, notifications, and interviews.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
# Student lifecycle

The schema catalog includes enrollment, transfer, academic-year closure, temporary historical edit grant, and transactional import payloads. These contracts preserve the existing student API while exposing the global student journey separately.

# Multi-school teaching

`TeacherAssignmentCreate` / `TeacherAssignmentResponse` describe a teacher's engagement at one school/model. They back the multi-school teaching endpoints and do not alter the existing `TeacherResponse` contract.
