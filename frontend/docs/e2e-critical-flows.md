# TeducAI — End-to-End Critical Workflow Tests

This document explains how to run the Playwright end-to-end test suite created for the main TeducAI validation scenarios.

## Purpose

The test suite validates a complete school-management workflow across the FastAPI backend and the Next.js frontend. It bootstraps a temporary school admin account, logs in through the browser UI, creates the required academic data through authenticated API calls, verifies the resulting records in the frontend, and validates the AI chat endpoint.

The current test file is:

```text
frontend/e2e/teducai-critical-flows.spec.ts
```

## Scenarios covered

| Scenario | Validation method |
|---|---|
| Create a school admin and authenticate | API bootstrap and browser login through `/login`. |
| Create a teacher | Authenticated API creation and frontend verification in the Teachers page. |
| Create a class | Authenticated API creation and frontend verification in the Classes page. |
| Create a subject | Authenticated API creation and frontend verification in the Subjects page. |
| Create an academic year and term | Authenticated API creation as prerequisites for assessments and report cards. |
| Create a student | Authenticated API creation and frontend verification in the Students page. |
| Create a timetable entry | Authenticated API creation and frontend verification in the Timetable page. |
| Create an assessment | Authenticated API creation and frontend verification in the Assessments page. |
| Enter marks | Authenticated bulk grade-entry API call. |
| Generate a report card | Authenticated report-card API call and frontend reports-page smoke check. |
| Record attendance | Authenticated attendance batch API call and frontend reports-page smoke check. |
| Add a fee | Authenticated API creation and frontend verification in the Fees page. |
| Record a payment | Authenticated fee-payment API call. |
| Add an expense | Authenticated API creation and frontend verification in the Expenses page. |
| Add a library book | Authenticated API creation and frontend verification in the Library page. |
| Issue and return a book loan | Authenticated API loan issuance and return. |
| Test AI chat | Direct API call to `/chat/` with response validation. |

## Installation

From the `frontend` directory, install Playwright if it has not already been installed:

```bash
cd /home/ubuntu/education-saas/frontend
npm install --save-dev @playwright/test
npx playwright install chromium
```

## Execution

Run the full E2E suite with:

```bash
cd /home/ubuntu/education-saas/frontend
npm run test:e2e
```

Run the headed version for visual debugging with:

```bash
npm run test:e2e:headed
```

Open the HTML report after a run with:

```bash
npm run test:e2e:report
```

## Environment variables

The script has sensible local defaults, but the following variables can be overridden:

| Variable | Default | Description |
|---|---|---|
| `E2E_BASE_URL` | `http://127.0.0.1:3000` | Frontend URL used by Playwright. |
| `E2E_API_URL` | `http://127.0.0.1:8000` | Backend API URL used by Playwright and the frontend. |
| `E2E_FRONTEND_PORT` | `3000` | Frontend dev-server port when Playwright starts the server. |
| `E2E_BACKEND_PORT` | `8000` | Backend server port when Playwright starts FastAPI. |
| `E2E_LOCALE` | `en` | Locale prefix used in frontend routes. |
| `E2E_ADMIN_EMAIL` | Generated dynamically | Optional existing admin email. If omitted, the test creates a temporary school. |
| `E2E_ADMIN_PASSWORD` | `Admin123!Secure` | Password for the generated or existing admin user. |

## Notes

The test intentionally combines browser validation with authenticated API setup. This keeps the suite reliable while still proving that the frontend can authenticate, load protected pages, and display records created through the real backend. For a later, stricter QA phase, the same scenarios can be expanded into fully browser-driven form interactions for every module.
