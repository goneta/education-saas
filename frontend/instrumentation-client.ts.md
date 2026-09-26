# instrumentation-client.ts

Initializes Sentry in the browser only when `NEXT_PUBLIC_SENTRY_DSN` is set.
Exports the App Router transition hook and applies `sentry-privacy.ts` to errors
and spans. Samples 10% of traces; no replay or logs. Requires the matching
ingest origin in `next.config.ts` CSP.
