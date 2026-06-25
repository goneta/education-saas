# auth-routing.ts

## Purpose

- Centralizes role and account-type dashboard destinations for authenticated users.
- Protects recruiter and external-student dashboard areas from manual cross-role navigation.

## Local Contracts

- Recruiters land on `/dashboard/emploi-recruteur`.
- External students land on `/dashboard/emploi`.
- Super Admin employment routes are checked before generic student employment routes so `/dashboard/emploi-admin` stays reachable by Super Admins and blocked for all other roles.
- Existing users with recruiter or external-student profile hints are routed by `account_type` even if their primary role predates the dedicated account flow.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint lib/auth-routing.ts"`
