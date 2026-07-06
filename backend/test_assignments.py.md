# test_assignments.py — Homework module tests

Covers: create→publish notifies the class; AI generate splits content vs
answer key (mocked AI); submit flow + late-lock; grade notifies student+parent
and push-to-gradebook creates an Assessment + Grade; AI grade is a proposal
until the teacher confirms; answer-key release control (never/after_due/
immediate); endpoint RBAC + student targeting (non-targeted student blocked,
student can't create, /mine scoping). In-memory SQLite; AI mocked; wallets
credited.
