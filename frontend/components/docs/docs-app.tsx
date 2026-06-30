"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { X } from "lucide-react"
import { DocsHeader } from "@/components/docs/docs-header"
import { DocsSidebar } from "@/components/docs/docs-sidebar"
import { DocsContent } from "@/components/docs/docs-content"
import { DocsToc } from "@/components/docs/docs-toc"
import { AskDocsButton } from "@/components/docs/ask-docs-button"
import { DOC_GROUPS, DOC_PAGES, DOC_TABS } from "@/lib/docs/content"

function tabForSlug(slug: string): string {
    for (const g of DOC_GROUPS) if (g.items.some(i => i.slug === slug)) return g.tab
    return DOC_TABS[0]
}

export function DocsApp({ locale, slug }: { locale: string; slug: string }) {
    const page = DOC_PAGES[slug]
    const [activeTab, setActiveTab] = useState(() => tabForSlug(slug))
    const [drawer, setDrawer] = useState(false)

    // Keep the active tab in sync with the page being viewed.
    useEffect(() => { setActiveTab(tabForSlug(slug)) }, [slug])
    // Lock body scroll while the mobile drawer is open.
    useEffect(() => { document.body.style.overflow = drawer ? "hidden" : ""; return () => { document.body.style.overflow = "" } }, [drawer])

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
                                <span className="text-sm font-bold text-[#0F172A] dark:text-white">Documentation</span>
                                <button onClick={() => setDrawer(false)} aria-label="Close"><X className="h-5 w-5 text-[#475569] dark:text-[#c7d0da]" /></button>
                            </div>
                            <div className="flex gap-1 overflow-x-auto px-3 pb-2">
                                {DOC_TABS.map(t => (
                                    <button key={t} onClick={() => setActiveTab(t)} className={`shrink-0 rounded-full px-3 py-1 text-[13px] ${activeTab === t ? "bg-[#F1F3F5] font-medium text-[#0F172A] dark:bg-[#252b30] dark:text-white" : "text-[#475569] dark:text-[#c7d0da]"}`}>{t}</button>
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
                                    <p className="text-lg font-semibold text-[#0F172A] dark:text-white">Page not found</p>
                                    <Link href={`/${locale}/docs`} className="mt-2 inline-block text-[#0F766E] underline">Back to the docs home</Link>
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

            <AskDocsButton locale={locale} />
        </div>
    )
}
