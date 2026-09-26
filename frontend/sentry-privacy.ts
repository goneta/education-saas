import type { ErrorEvent } from '@sentry/nextjs';

export const sentryDataCollection = {
  userInfo: false,
  cookies: false,
  httpHeaders: false,
  httpBodies: [],
  urlQueryParams: false,
  graphQL: { document: false, variables: false },
  genAI: { inputs: false, outputs: false },
  databaseQueryData: false,
  queues: false,
  stackFrameVariables: false,
  frameContextLines: 0,
};

export function scrubSentryError(event: ErrorEvent): ErrorEvent {
  return {
    type: undefined,
    event_id: event.event_id,
    timestamp: event.timestamp,
    platform: event.platform,
    level: event.level,
    release: event.release,
    environment: event.environment,
    exception: event.exception && {
      values: event.exception.values?.map((exception) => ({
        type: exception.type,
        value: exception.type || 'ApplicationError',
        stacktrace: exception.stacktrace && {
          frames: exception.stacktrace.frames?.map((frame) => ({
            filename: frame.filename,
            function: frame.function,
            lineno: frame.lineno,
            colno: frame.colno,
            in_app: frame.in_app,
          })),
        },
      })),
    },
  };
}

export function scrubSentrySpan<T extends {
  is_segment: boolean;
  name: string;
  attributes: Record<string, unknown>;
  links?: unknown;
}>(span: T): T {
  const isRoute = span.is_segment && span.attributes['sentry.segment.name.source'] === 'route';
  return {
    ...span,
    name: isRoute ? span.name : '[redacted]',
    attributes: {},
    links: undefined,
  } as T;
}
