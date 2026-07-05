"use client"

import Link from "next/link"
import { useEffect, useRef, useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import { Braces, Menu, Monitor, ChevronDown, Sparkles } from "lucide-react"
import { DOC_TABS } from "@/lib/docs/content"
import { docsUi, getTabLabel } from "@/lib/docs/registry"

const LANGUAGES: { code: string; label: string }[] = [
    { code: "fr", label: "Français" },
    { code: "en", label: "English" },
    { code: "es", label: "Español" },
    { code: "sw", label: "Kiswahili" },
]

export function DocsHeader({ locale, activeTab, onTab, onMenu }: {
    locale: string
    activeTab: string
    onTab: (tab: string) => void
    onMenu: () => void
}) {
    const router = useRouter()
    const pathname = usePathname()
    const [langOpen, setLangOpen] = useState(false)
    const langRef = useRef<HTMLDivElement | null>(null)

    // Close the language menu on outside click.
    useEffect(() => {
        if (!langOpen) return
        const close = (event: MouseEvent) => {
            if (langRef.current && !langRef.current.contains(event.target as Node)) setLangOpen(false)
        }
        document.addEventListener("mousedown", close)
        return () => document.removeEventListener("mousedown", close)
    }, [langOpen])

    const currentLanguage = LANGUAGES.find(l => l.code === locale)?.label || "English"

    const switchLocale = (code: string) => {
        setLangOpen(false)
        if (code === locale) return
        // Swap the locale segment of the current path: /{locale}/docs/... -> /{code}/docs/...
        const segments = (pathname || `/${locale}/docs`).split("/")
        if (segments.length > 1) segments[1] = code
        router.push(segments.join("/") || `/${code}/docs`)
    }

    return (
        <header className="sticky top-0 z-40 border-b border-[#E5E7EB] bg-white/95 backdrop-blur dark:border-[#3b4248] dark:bg-[#0f1419]/95">
            <div className="flex h-16 items-center gap-4 px-4 sm:px-6">
                <button onClick={onMenu} className="rounded-lg p-2 text-[#475569] hover:bg-[#F1F3F5] lg:hidden dark:text-[#c7d0da] dark:hover:bg-[#252b30]" aria-label="Open menu">
                    <Menu className="h-5 w-5" />
                </button>
                <Link href={`/${locale}/docs`} className="flex items-center gap-2.5 shrink-0">
                    <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#0F766E] text-white"><Sparkles className="h-4 w-4" /></span>
                    <span className="text-[15px] font-bold tracking-tight text-[#0F172A] dark:text-white">TeducAI Platform Docs</span>
                </Link>

                <nav className="ml-2 hidden items-center gap-1 md:flex">
                    {DOC_TABS.map(tab => (
                        <button key={tab} onClick={() => onTab(tab)}
                            className={`flex items-center gap-1 rounded-full px-3.5 py-1.5 text-[14px] font-medium transition ${activeTab === tab ? "bg-[#F1F3F5] text-[#0F172A] dark:bg-[#252b30] dark:text-white" : "text-[#475569] hover:text-[#0F172A] dark:text-[#c7d0da] dark:hover:text-white"}`}>
                            {getTabLabel(tab, locale)}
                            {tab === "Resources" && <ChevronDown className="h-3.5 w-3.5 opacity-60" />}
                        </button>
                    ))}
                </nav>

                <div className="ml-auto flex items-center gap-1 sm:gap-3">
                    <a href="#api" className="hidden items-center gap-1.5 text-[14px] text-[#475569] hover:text-[#0F172A] sm:flex dark:text-[#c7d0da] dark:hover:text-white">
                        <Braces className="h-4 w-4" /> {docsUi("apiReference", locale)}
                    </a>
                    <button className="hidden rounded-lg p-2 text-[#475569] hover:bg-[#F1F3F5] sm:block dark:text-[#c7d0da] dark:hover:bg-[#252b30]" aria-label="Display mode"><Monitor className="h-4 w-4" /></button>

                    <div ref={langRef} className="relative hidden sm:block">
                        <button onClick={() => setLangOpen(v => !v)} aria-expanded={langOpen}
                            className="flex items-center gap-1 text-[14px] text-[#475569] hover:text-[#0F172A] dark:text-[#c7d0da] dark:hover:text-white">
                            {currentLanguage} <ChevronDown className={`h-3.5 w-3.5 transition ${langOpen ? "rotate-180" : ""}`} />
                        </button>
                        {langOpen && (
                            <div className="absolute right-0 top-8 z-50 w-40 rounded-xl border border-[#E5E7EB] bg-white py-1 shadow-lg dark:border-[#3b4248] dark:bg-[#1c2227]">
                                {LANGUAGES.map(lang => (
                                    <button key={lang.code} onClick={() => switchLocale(lang.code)}
                                        className={`block w-full px-4 py-2 text-left text-[14px] hover:bg-[#F8FAFC] dark:hover:bg-[#252b30] ${lang.code === locale ? "font-semibold text-[#0F766E]" : "text-[#374151] dark:text-[#c7d0da]"}`}>
                                        {lang.label}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    <Link href={`/${locale}/dashboard`} className="flex items-center gap-1.5 rounded-full bg-[#0F172A] px-4 py-1.5 text-[14px] font-medium text-white hover:bg-[#0F172A]/90 dark:bg-white dark:text-[#0F172A] dark:hover:bg-white/90">
                        <Monitor className="h-3.5 w-3.5" /> {docsUi("console", locale)}
                    </Link>
                </div>
            </div>
        </header>
    )
}
