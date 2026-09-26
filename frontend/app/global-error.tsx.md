# global-error.tsx

Root App Router error boundary. Captures uncaught render errors and offers a
retry action without relying on the locale layout or authenticated providers.
The error event passes through the browser Sentry privacy scrubber.
