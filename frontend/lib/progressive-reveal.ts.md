# progressive-reveal.ts

## Purpose

- Reveals already-received AI preview text gradually so the preview panel renders progressively instead of in a single block.

## Local Contracts

- This is a client-side rendering effect; the `/chat` response is not token-streamed. Provider token streaming would require a dedicated SSE endpoint and is out of scope here.
- `revealProgressively` returns a cancel function so a new message immediately supersedes an in-flight reveal; callers must cancel on unmount and before starting a new reveal.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint lib/progressive-reveal.ts"`
