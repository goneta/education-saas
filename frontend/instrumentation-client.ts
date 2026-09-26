import * as Sentry from '@sentry/nextjs';
import { scrubSentryError, scrubSentrySpan, sentryDataCollection } from './sentry-privacy';

if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    release: process.env.NEXT_PUBLIC_SENTRY_RELEASE,
    environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || process.env.NODE_ENV,
    dataCollection: sentryDataCollection,
    tracesSampleRate: 0.1,
    beforeSend: scrubSentryError,
    beforeSendSpan: scrubSentrySpan,
    beforeBreadcrumb: () => null,
  });
}

export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;
