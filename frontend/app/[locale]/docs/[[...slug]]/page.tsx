import { DocsApp } from "@/components/docs/docs-app"
import { normalizeLocale } from "@/lib/i18n"
import { DEFAULT_SLUG } from "@/lib/docs/content"

export default async function DocsPage({ params }: { params: Promise<{ locale: string; slug?: string[] }> }) {
    const { locale: rawLocale, slug } = await params
    const locale = normalizeLocale(rawLocale)
    const current = slug && slug.length > 0 ? slug[0] : DEFAULT_SLUG
    return <DocsApp locale={locale} slug={current} />
}
