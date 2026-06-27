# test_ai_credit_sync.py

## Purpose

- Verifies `balance_api_supported` matches provider reality (OpenRouter yes; OpenAI/Anthropic/Gemini/Grok/xAI/Manus no).
- Verifies an OpenRouter sync fetches and applies the remaining balance (mocked HTTP), an unsupported provider keeps its manual value, and a supported provider without a key reports `no_key`.
- Verifies platform monitoring totals sum provider credits and deduct successful purchases from the global remaining pool.

## Verification

- `python -m pytest backend/test_ai_credit_sync.py`
