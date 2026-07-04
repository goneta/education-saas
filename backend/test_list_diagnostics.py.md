# test_list_diagnostics.py — Tests for the empty-list diagnostics endpoints

Covers: healthy school (final count matches, no hints); student living under a
different school than the active context (hint + school id surfaced); student
users without student_profiles rows (manual-import hint); teachers happy path;
teacher role denied (403).
