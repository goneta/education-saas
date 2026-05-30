import { getRequestConfig } from 'next-intl/server';

export default getRequestConfig(async ({ locale }) => {
    return {
        locale: locale as string,
        messages: (await import(`./messages/${locale as string}.json`)).default
    };
});
