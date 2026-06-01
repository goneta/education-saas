import { DEFAULT_LOCALE, normalizeLocale } from "@/lib/i18n"

const NUMBER_LOCALES = {
  fr: "fr-FR",
  en: "en-US",
  es: "es-ES",
}

export const DEFAULT_CURRENCY = "FCFA"
export const DEFAULT_CURRENCY_CODE = "XOF"

export function formatNumber(value: number, locale: string | string[] | undefined = DEFAULT_LOCALE) {
  const normalized = normalizeLocale(locale)
  return new Intl.NumberFormat(NUMBER_LOCALES[normalized]).format(value)
}

export function formatCurrency(value: number, locale: string | string[] | undefined = DEFAULT_LOCALE) {
  return `${formatNumber(value, locale)} ${DEFAULT_CURRENCY}`
}

export function formatDateTime(value: string | Date, locale: string | string[] | undefined = DEFAULT_LOCALE) {
  const normalized = normalizeLocale(locale)
  return new Intl.DateTimeFormat(NUMBER_LOCALES[normalized], {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

export function formatDate(value: string | Date, locale: string | string[] | undefined = DEFAULT_LOCALE) {
  const normalized = normalizeLocale(locale)
  return new Intl.DateTimeFormat(NUMBER_LOCALES[normalized], {
    dateStyle: "medium",
  }).format(new Date(value))
}
