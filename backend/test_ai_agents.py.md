# test_ai_agents.py

## Purpose

- Verifies the registry holds exactly 41 unique agents, each with the shared security contract in its prompt, a permission and keywords.
- Verifies `select_agent` routes by keyword, falls back to the coordinator on no match, is permission-aware (selects the right agent but flags unauthorized + refusal for under-privileged users), and that `accessible_agents` filters by permission.
- Verifies the LLM-first router via an injected `classifier`: a valid key overrides keyword routing (`method == "llm"`), an invalid key falls back to keyword scoring, and a raising classifier never breaks routing (`method == "keyword"`).

## Verification

- `python -m pytest backend/test_ai_agents.py`
