import { DEFAULT_LOCALE, normalizeLocale } from "@/lib/i18n"

const NUMBER_LOCALES = {
  fr: "fr-FR",
  en: "en-US",
  es: "es-ES",
  sw: "sw-KE",
}

export const DEFAULT_CURRENCY = "FCFA"
export const DEFAULT_CURRENCY_CODE = "XOF"
const CURRENCY_TO_ISO: Record<string, string> = {
  FCFA: "XOF",
  GBP: "GBP",
  EUR: "EUR",
  USD: "USD",
}

export function formatNumber(value: number, locale: string | string[] | undefined = DEFAULT_LOCALE) {
  const normalized = normalizeLocale(locale)
  return new Intl.NumberFormat(NUMBER_LOCALES[normalized]).format(value)
}

export function formatCurrency(value: number, locale: string | string[] | undefined = DEFAULT_LOCALE, currency = DEFAULT_CURRENCY) {
  const normalized = normalizeLocale(locale)
  const isoCurrency = CURRENCY_TO_ISO[currency] || currency || DEFAULT_CURRENCY_CODE
  if (currency === "FCFA") return `${formatNumber(value, locale)} FCFA`
  return new Intl.NumberFormat(NUMBER_LOCALES[normalized], {
    style: "currency",
    currency: isoCurrency,
  }).format(value)
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
