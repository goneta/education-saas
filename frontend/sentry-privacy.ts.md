# sentry-privacy.ts

Shared browser/Node/Edge Sentry data policy. Disables automatic collection of
user, HTTP, query, database, AI, queue, stack-local, and source-context data.
Whitelists only error type and stack position in error events; streamed spans
retain route-template names only, with all arbitrary attributes removed.
Changes require a privacy regression check using representative school data.
