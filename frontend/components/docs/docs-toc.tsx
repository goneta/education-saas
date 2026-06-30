"use client"

import { useEffect, useMemo, useState } from "react"
import { List } from "lucide-react"
import { slugify, type DocBlock } from "@/components/docs/doc-blocks"

export function DocsToc({ blocks }: { blocks: DocBlock[] }) {
    const headings = useMemo(
        () => blocks.filter(b => b.k === "h2" || b.k === "h3").map(b => ({ id: slugify((b as { text: string }).text), text: (b as { text: string }).text, level: b.k })),
        [blocks],
    )
    const [active, setActive] = useState<string>("")

    useEffect(() => {
        if (headings.length === 0) return
        const observer = new IntersectionObserver(
            entries => {
                const visible = entries.filter(e => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
                if (visible[0]) setActive(visible[0].target.id)
            },
            { rootMargin: "-80px 0px -70% 0px", threshold: 0 },
        )
        headings.forEach(h => { const el = document.getElementById(h.id); if (el) observer.observe(el) })
        return () => observer.disconnect()
    }, [headings])

    if (headings.length === 0) return null

    return (
        <nav className="sticky top-24 hidden max-h-[calc(100vh-7rem)] overflow-y-auto xl:block">
            <p className="mb-3 flex items-center gap-2 text-[12px] font-semibold uppercase tracking-wide text-[#94A3B8]"><List className="h-4 w-4" /> On this page</p>
            <ul className="space-y-1 border-l border-[#E5E7EB] dark:border-[#3b4248]">
                {headings.map(h => {
                    const isActive = active === h.id
                    return (
                        <li key={h.id}>
                            <a href={`#${h.id}`}
                                className={`-ml-px block border-l-2 py-1 text-[13px] transition ${h.level === "h3" ? "pl-6" : "pl-4"} ${isActive ? "border-[#0F766E] font-medium text-[#0F172A] dark:text-white" : "border-transparent text-[#64748B] hover:text-[#0F172A] dark:text-[#94A3B8] dark:hover:text-white"}`}>
                                {h.text}
                            </a>
                        </li>
                    )
                })}
            </ul>
        </nav>
    )
}
