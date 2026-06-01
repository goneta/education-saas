import createMiddleware from 'next-intl/middleware';
import { DEFAULT_LOCALE, SUPPORTED_LOCALES } from './lib/i18n';

export default createMiddleware({
    locales: SUPPORTED_LOCALES,
    defaultLocale: DEFAULT_LOCALE,
    localePrefix: 'always'
});

export const config = {
    matcher: ['/', '/(fr|en|es)/:path*']
};
