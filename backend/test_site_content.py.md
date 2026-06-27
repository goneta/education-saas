# test_site_content.py

## Purpose

- Verifies the public Site CMS returns code-level defaults when no content has been saved.
- Verifies a Super Admin can update content, that unspecified fields keep their defaults via deep merge, and that saved changes are visible through the public read.
- Verifies non-Super-Admin users cannot update site content (403).
- Verifies unknown top-level sections are ignored on save.

## Verification

- `python -m pytest backend/test_site_content.py`
