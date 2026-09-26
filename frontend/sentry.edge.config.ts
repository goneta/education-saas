import * as Sentry from '@sentry/nextjs';
import { scrubSentryError, scrubSentrySpan, sentryDataCollection } from './sentry-privacy';

const dsn = process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    release: process.env.SENTRY_RELEASE,
    environment: process.env.APP_ENV || process.env.NODE_ENV,
    dataCollection: sentryDataCollection,
    tracesSampleRate: 0.1,
    beforeSend: scrubSentryError,
    beforeSendSpan: scrubSentrySpan,
    beforeBreadcrumb: () => null,
  });
}
