# communication.py

## Source File
- `backend/routers/communication.py`

## Purpose
- Communication Platform (`/communication`): announcement center — create (draft/scheduled), list, and publish-with-fan-out to an audience (all/teachers/parents/students) via `automation.record_notification`. Emergency flag changes the event type.

## Local Contracts
- Tenant-scoped; writes gated to publisher roles. Publish is idempotent. External channel adapters (WhatsApp/voice/video) and class-membership targeting are roadmap refinements.

## Verification
- `python -m pytest backend/test_communication.py`
