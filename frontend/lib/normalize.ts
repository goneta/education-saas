/**
 * Shared text normalization for accent- and case-insensitive search across the
 * app (context selector, universal table filter, any search-as-you-type input).
 *
 * Folds diacritics (é → e, ç → c), lowercases, and trims, so "Étoile" matches a
 * query of "etoile". Used by both the global institution selector and the
 * reusable TableFilter so all search behaves identically.
 */
const DIACRITICS = /\p{Diacritic}/gu

export function normalizeText(value: unknown): string {
    if (value === null || value === undefined) return ""
    return String(value)
        .normalize("NFD")
        .replace(DIACRITICS, "")
        .toLowerCase()
        .trim()
}

/** True when `haystack` contains `needle`, accent- and case-insensitively. */
export function matchesText(haystack: unknown, needle: string): boolean {
    const query = normalizeText(needle)
    if (!query) return true
    return normalizeText(haystack).includes(query)
}
