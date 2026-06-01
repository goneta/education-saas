export const SUPPORTED_LOCALES = ["fr", "en", "es", "sw"] as const

export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number]

export const DEFAULT_LOCALE: SupportedLocale = "fr"

export const LOCALE_LABELS: Record<SupportedLocale, string> = {
  fr: "Francais",
  en: "English",
  es: "Espanol",
  sw: "Kiswahili",
}

export function normalizeLocale(locale?: string | string[]): SupportedLocale {
  const value = Array.isArray(locale) ? locale[0] : locale
  return SUPPORTED_LOCALES.includes(value as SupportedLocale) ? value as SupportedLocale : DEFAULT_LOCALE
}
