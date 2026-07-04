# 20260704_0049_cart_student_enrollment.py

Repair migration for a model-vs-migrations drift: `CartItem.student_enrollment_id`
existed on the model but no migration ever added the column, so Postgres
production databases (built via alembic) 500ed on every `GET /account/cart`
with UndefinedColumn while SQLite dev databases (built from the models) worked.
Idempotent (`_has_column` guard) so model-built databases upgrade cleanly.
A full alembic-vs-models schema diff confirms this was the ONLY drift.
