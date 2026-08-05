import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./i18n.ts');

// Audit SEC-06: security headers were only set by the FastAPI middleware, so
// they applied to API responses and NOT to the HTML pages Next.js serves —
// precisely where XSS and clickjacking matter. They are declared here for every
// page. The CSP keeps 'unsafe-inline'/'unsafe-eval' for scripts because the Next
// runtime injects inline bootstrap code; tightening it further requires the
// nonce-based setup and is tracked as a follow-up.
const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
  { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' },
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self' data:",
      "connect-src 'self'",
      "frame-ancestors 'none'",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ].join('; '),
  },
];

/** @type {import('next').NextConfig} */
const nextConfig = {
  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }];
  },
  async rewrites() {
    // Audit CFG-03: the old fallback was :8000 while PM2 serves the backend on
    // :8001, so a missing variable silently proxied to ANOTHER app's backend.
    // Development keeps a fallback; production must be explicit.
    const backendUrl = process.env.BACKEND_INTERNAL_URL
      || (process.env.NODE_ENV === 'production'
        ? (() => { throw new Error('BACKEND_INTERNAL_URL must be set in production'); })()
        : 'http://127.0.0.1:8000');

    return [
      {
        source: '/api/backend/:path*',
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default withNextIntl(nextConfig);
