"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { List, X } from "lucide-react"
import { slugify } from "@/components/docs/doc-blocks"
import { DocsHeader } from "@/components/docs/docs-header"
import { DocsSidebar } from "@/components/docs/docs-sidebar"
import { DocsContent } from "@/components/docs/docs-content"
import { DocsToc } from "@/components/docs/docs-toc"
import { AskDocsButton } from "@/components/docs/ask-docs-button"
import { DOC_GROUPS, DOC_TABS } from "@/lib/docs/content"
import { docsUi, getDocPage, getTabLabel } from "@/lib/docs/registry"

function tabForSlug(slug: string): string {
    for (const g of DOC_GROUPS) if (g.items.some(i => i.slug === slug)) return g.tab
    return DOC_TABS[0]
}

export function DocsApp({ locale, slug }: { locale: string; slug: string }) {
    const page = getDocPage(locale, slug)
    const [activeTab, setActiveTab] = useState(() => tabForSlug(slug))
    const [drawer, setDrawer] = useState(false)
    const [tocOpen, setTocOpen] = useState(false)

    // In-page anchors for the mobile floating TOC.
    const headings = useMemo(
        () => (page ? page.blocks.filter(b => b.k === "h2" || b.k === "h3").map(b => ({ id: slugify((b as { text: string }).text), text: (b as { text: string }).text, level: b.k })) : []),
        [page],
    )

    // Keep the active tab in sync with the page being viewed.
    useEffect(() => { setActiveTab(tabForSlug(slug)) }, [slug])
    // Lock body scroll while the mobile drawer or TOC sheet is open.
    useEffect(() => { document.body.style.overflow = drawer || tocOpen ? "hidden" : ""; return () => { document.body.style.overflow = "" } }, [drawer, tocOpen])

    return (
        <div className="min-h-screen bg-white dark:bg-[#0f1419]">
            <DocsHeader locale={locale} activeTab={activeTab} onTab={setActiveTab} onMenu={() => setDrawer(true)} />

            <div className="mx-auto flex w-full max-w-[1440px]">
                {/* Left sidebar (desktop) */}
                <aside className="sticky top-16 hidden h-[calc(100vh-4rem)] w-[280px] shrink-0 border-r border-[#E5E7EB] dark:border-[#3b4248] lg:block">
                    <DocsSidebar locale={locale} activeTab={activeTab} activeSlug={slug} />
                </aside>

                {/* Mobile drawer */}
                {drawer && (
                    <div className="fixed inset-0 z-50 lg:hidden">
                        <div className="absolute inset-0 bg-black/40" onClick={() => setDrawer(false)} />
                        <div className="absolute left-0 top-0 h-full w-[300px] max-w-[85vw] border-r border-[#E5E7EB] bg-white dark:border-[#3b4248] dark:bg-[#0f1419]">
                            <div className="flex items-center justify-between px-4 py-3">
                                <span className="text-sm font-bold text-[#0F172A] dark:text-white">{docsUi("documentation", locale)}</span>
                                <button onClick={() => setDrawer(false)} aria-label="Close"><X className="h-5 w-5 text-[#475569] dark:text-[#c7d0da]" /></button>
                            </div>
                            <div className="flex gap-1 overflow-x-auto px-3 pb-2">
                                {DOC_TABS.map(t => (
                                    <button key={t} onClick={() => setActiveTab(t)} className={`shrink-0 rounded-full px-3 py-1 text-[13px] ${activeTab === t ? "bg-[#F1F3F5] font-medium text-[#0F172A] dark:bg-[#252b30] dark:text-white" : "text-[#475569] dark:text-[#c7d0da]"}`}>{getTabLabel(t, locale)}</button>
                                ))}
                            </div>
                            <div className="h-[calc(100%-6.5rem)]">
                                <DocsSidebar locale={locale} activeTab={activeTab} activeSlug={slug} onNavigate={() => setDrawer(false)} />
                            </div>
                        </div>
                    </div>
                )}

                {/* Center + right */}
                <div className="min-w-0 flex-1">
                    <div className="mx-auto flex w-full max-w-[1100px] gap-10 px-5 py-10 sm:px-8">
                        <main className="min-w-0 flex-1">
                            {page ? <DocsContent page={page} locale={locale} /> : (
                                <div className="py-20 text-center">
                                    <p className="text-lg font-semibold text-[#0F172A] dark:text-white">{docsUi("pageNotFound", locale)}</p>
                                    <Link href={`/${locale}/docs`} className="mt-2 inline-block text-[#0F766E] underline">{docsUi("backHome", locale)}</Link>
                                </div>
                            )}
                        </main>
                        {page && (
                            <div className="w-[200px] shrink-0">
                                <DocsToc blocks={page.blocks} />
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Mobile floating TOC (the right sidebar is desktop-only) */}
            {headings.length > 0 && (
                <>
                    {tocOpen && (
                        <div className="fixed inset-0 z-50 xl:hidden">
                            <div className="absolute inset-0 bg-black/40" onClick={() => setTocOpen(false)} />
                            <div className="absolute bottom-0 left-0 right-0 max-h-[60vh] overflow-y-auto rounded-t-2xl border-t border-[#E5E7EB] bg-white p-5 dark:border-[#3b4248] dark:bg-[#0f1419]">
                                <div className="mb-3 flex items-center justify-between">
                                    <p className="flex items-center gap-2 text-[12px] font-semibold uppercase tracking-wide text-[#94A3B8]"><List className="h-4 w-4" /> {docsUi("onThisPage", locale)}</p>
                                    <button onClick={() => setTocOpen(false)} aria-label="Close"><X className="h-4 w-4 text-[#94A3B8]" /></button>
                                </div>
                                <ul className="space-y-1">
                                    {headings.map(h => (
                                        <li key={h.id}>
                                            <a href={`#${h.id}`} onClick={() => setTocOpen(false)}
                                                className={`block rounded-lg px-3 py-2 text-[14px] text-[#374151] hover:bg-[#F8FAFC] dark:text-[#c7d0da] dark:hover:bg-[#1c2227] ${h.level === "h3" ? "pl-7" : ""}`}>
                                                {h.text}
                                            </a>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    )}
                    <button onClick={() => setTocOpen(true)} aria-label={docsUi("onThisPage", locale)}
                        className="fixed bottom-6 left-6 z-40 flex items-center gap-2 rounded-full border border-[#E5E7EB] bg-white px-4 py-3 text-sm font-medium text-[#0F172A] shadow-lg xl:hidden dark:border-[#3b4248] dark:bg-[#1c2227] dark:text-white">
                        <List className="h-4 w-4" /> {docsUi("onThisPage", locale)}
                    </button>
                </>
            )}

            <AskDocsButton locale={locale} />
        </div>
    )
}
