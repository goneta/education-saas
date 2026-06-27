# site.py

## Source File

- `backend/routers/site.py`

## Purpose

- Python source file used by the backend; participates in the FastAPI API boundary.
- Exposes the public Site TeducAI CMS: a public `GET /site/content` and a Super Admin-only `PUT /site/content` that persist the editable marketing-site content (hero, partners, FAQ, testimonials, pricing note, SEO meta, footer).

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Content is stored as a single `SiteContent` JSON document (singleton row). `GET` always returns code-level `DEFAULT_SITE_CONTENT` deep-merged with saved values so the public site never breaks when the table is empty.
- `PUT` is Super Admin only, persists only recognised top-level sections (unknown keys are ignored), deep-merges over existing content, and records a `site_content.updated` audit event.
- The public read endpoint must remain unauthenticated; the write endpoint must keep the Super Admin gate.

## Verification

- python -m py_compile backend\routers\site.py; python -c "import backend.main as m; print(m.app.title)"
- python -m pytest backend/test_site_content.py
