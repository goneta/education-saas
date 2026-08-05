# requirements.txt

## Source File

- `backend/requirements.txt`

## Purpose

- Plain text source or support file.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
- CFG-02: toutes les versions sont desormais EPINGLEES (celles avec lesquelles la suite est verte); `openai-agents` reste a installer separement avec --no-deps (conflit de pins transitifs avec la pile FastAPI 0.104), procedure documentee en tete de fichier. ARCH-04: `motor` (MongoDB) et `langchain`, importes nulle part, ont ete retires.
