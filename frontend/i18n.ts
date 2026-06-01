import { getRequestConfig } from 'next-intl/server';
import { DEFAULT_LOCALE, normalizeLocale } from './lib/i18n';

export default getRequestConfig(async ({ locale }) => {
    const normalizedLocale = normalizeLocale(locale || DEFAULT_LOCALE);
    return {
        locale: normalizedLocale,
        messages: (await import(`./messages/${normalizedLocale}.json`)).default
    };
});
