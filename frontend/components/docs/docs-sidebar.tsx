"use client"

import Link from "next/link"
import { useMemo, useState } from "react"
import { Search, ChevronDown, Building2 } from "lucide-react"
import { DOC_GROUPS, DOC_PAGES } from "@/lib/docs/content"

export function DocsSidebar({ locale, activeTab, activeSlug, onNavigate }: {
    locale: string
    activeTab: string
    activeSlug: string
    onNavigate?: () => void
}) {
    const [query, setQuery] = useState("")

    const groups = useMemo(() => {
        const inTab = DOC_GROUPS.filter(g => g.tab === activeTab)
        const q = query.trim().toLowerCase()
        if (!q) return inTab
        return inTab
            .map(g => ({ ...g, items: g.items.filter(it => it.label.toLowerCase().includes(q) || (DOC_PAGES[it.slug]?.description || "").toLowerCase().includes(q)) }))
            .filter(g => g.items.length > 0)
    }, [activeTab, query])

    return (
        <div className="flex h-full flex-col">
            <div className="p-4">
                <div className="relative">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#94A3B8]" />
                    <input
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        placeholder="Search…"
                        className="h-10 w-full rounded-xl border border-[#E5E7EB] bg-white pl-9 pr-12 text-sm text-[#0F172A] outline-none focus:border-[#0F766E] dark:border-[#3b4248] dark:bg-[#1c2227] dark:text-white"
                    />
                    <kbd className="absolute right-3 top-1/2 -translate-y-1/2 rounded border border-[#E5E7EB] px-1.5 py-0.5 text-[11px] text-[#94A3B8] dark:border-[#3b4248]">⌘K</kbd>
                </div>
            </div>

            <nav className="flex-1 overflow-y-auto px-3 pb-6">
                {groups.map(group => (
                    <div key={group.title} className="mb-5">
                        <p className="px-3 pb-1.5 text-[13px] font-bold uppercase tracking-wide text-[#0F172A] dark:text-white">{group.title}</p>
                        <ul className="space-y-0.5">
                            {group.items.map(item => {
                                const active = item.slug === activeSlug
                                return (
                                    <li key={item.slug}>
                                        <Link href={`/${locale}/docs/${item.slug}`} onClick={onNavigate}
                                            className={`block rounded-lg px-3 py-1.5 text-[14px] transition ${active ? "bg-[#F1F3F5] font-medium text-[#0F172A] dark:bg-[#252b30] dark:text-white" : "text-[#475569] hover:bg-[#F8FAFC] hover:text-[#0F172A] dark:text-[#c7d0da] dark:hover:bg-[#1c2227] dark:hover:text-white"}`}>
                                            {item.label}
                                        </Link>
                                    </li>
                                )
                            })}
                        </ul>
                    </div>
                ))}
                {groups.length === 0 && <p className="px-3 text-sm text-[#94A3B8]">No results.</p>}
            </nav>

            <div className="border-t border-[#E5E7EB] p-3 dark:border-[#3b4248]">
                <button className="flex w-full items-center gap-3 rounded-xl px-2 py-2 text-left hover:bg-[#F8FAFC] dark:hover:bg-[#1c2227]">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#0F766E]/10 text-[#0F766E]"><Building2 className="h-4 w-4" /></span>
                    <span className="min-w-0 flex-1">
                        <span className="block truncate text-[13px] font-semibold text-[#0F172A] dark:text-white">TeducAI</span>
                        <span className="block truncate text-[12px] text-[#94A3B8]">Documentation</span>
                    </span>
                    <ChevronDown className="h-4 w-4 text-[#94A3B8]" />
                </button>
            </div>
        </div>
    )
}
