# sentry.server.config.ts

Node runtime Sentry initialization, loaded through `instrumentation.ts`.
Uses `SENTRY_DSN` or the public DSN fallback, a 10% trace sample, and shared
privacy scrubbers. Disabled when neither DSN is configured.
