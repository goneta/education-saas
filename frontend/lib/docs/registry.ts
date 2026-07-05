// Locale-aware resolver over the docs content.
//
// English (`content.ts`) is the source of truth and the fallback. Translations
// live in per-locale modules (`content.<locale>.ts`) and are merged OVER the
// English maps, so a page not yet translated in a locale gracefully falls back
// to English rather than 404-ing — the same graceful-fallback pattern the
// in-app Help Center uses.

import { DOC_GROUPS, DOC_PAGES, type DocGroup, type DocPage } from "./content"
import { DOC_GROUPS_FR, DOC_PAGES_FR, TAB_LABELS_FR, DOCS_UI_FR } from "./content.fr"

const PAGES_BY_LOCALE: Record<string, Record<string, DocPage>> = {
    fr: DOC_PAGES_FR,
}

const GROUPS_BY_LOCALE: Record<string, DocGroup[]> = {
    fr: DOC_GROUPS_FR,
}

const TAB_LABELS_BY_LOCALE: Record<string, Record<string, string>> = {
    fr: TAB_LABELS_FR,
}

// English chrome strings (fallback for every locale not translated below).
const DOCS_UI_EN: Record<string, string> = {
    search: "Search…",
    noResults: "No results.",
    copyPage: "Copy page",
    copied: "Copied",
    onThisPage: "On this page",
    documentation: "Documentation",
    pageNotFound: "Page not found",
    backHome: "Back to the docs home",
    apiReference: "API reference",
    console: "Console",
}

const DOCS_UI_BY_LOCALE: Record<string, Record<string, string>> = {
    fr: DOCS_UI_FR,
}

/** All doc pages for a locale, with per-page English fallback. */
export function getDocPages(locale: string): Record<string, DocPage> {
    const localized = PAGES_BY_LOCALE[locale]
    return localized ? { ...DOC_PAGES, ...localized } : DOC_PAGES
}

export function getDocPage(locale: string, slug: string): DocPage | undefined {
    return getDocPages(locale)[slug]
}

/** Sidebar groups (localized titles + item labels); tab keys stay English. */
export function getDocGroups(locale: string): DocGroup[] {
    return GROUPS_BY_LOCALE[locale] ?? DOC_GROUPS
}

/** Localized display label for a top-level tab key. */
export function getTabLabel(tab: string, locale: string): string {
    return TAB_LABELS_BY_LOCALE[locale]?.[tab] ?? tab
}

/** Localized chrome string, falling back to English. */
export function docsUi(key: keyof typeof DOCS_UI_EN, locale: string): string {
    return DOCS_UI_BY_LOCALE[locale]?.[key] ?? DOCS_UI_EN[key]
}
