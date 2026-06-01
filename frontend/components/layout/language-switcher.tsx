"use client"

import { useParams, usePathname, useRouter } from "next/navigation"
import { LOCALE_LABELS, normalizeLocale, SUPPORTED_LOCALES, type SupportedLocale } from "@/lib/i18n"

export function LanguageSwitcher() {
    const router = useRouter()
    const pathname = usePathname()
    const params = useParams()
    const currentLocale = normalizeLocale(params.locale as string)

    const switchLocale = (locale: SupportedLocale) => {
        const segments = pathname.split("/")
        if (SUPPORTED_LOCALES.includes(segments[1] as SupportedLocale)) {
            segments[1] = locale
            router.push(segments.join("/") || `/${locale}`)
            return
        }
        router.push(`/${locale}${pathname}`)
    }

    return (
        <select
            aria-label="Language"
            value={currentLocale}
            onChange={(event) => switchLocale(event.target.value as SupportedLocale)}
            className="h-9 rounded-md border border-[#E5E7EB] bg-white px-2 text-sm text-[#111827]"
        >
            {SUPPORTED_LOCALES.map(locale => (
                <option key={locale} value={locale}>{LOCALE_LABELS[locale]}</option>
            ))}
        </select>
    )
}
