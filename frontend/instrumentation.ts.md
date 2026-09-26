# instrumentation.ts

Next.js instrumentation hook. Loads the Node or Edge Sentry config for its
runtime and exports `Sentry.captureRequestError` for request exceptions. Does
not load server instrumentation into the browser bundle.
