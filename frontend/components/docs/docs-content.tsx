"use client"

import { useState } from "react"
import { Copy, Check, ChevronDown } from "lucide-react"
import { DocBlocks } from "@/components/docs/doc-blocks"
import type { DocPage } from "@/lib/docs/content"
import { docsUi } from "@/lib/docs/registry"

function toMarkdown(page: DocPage): string {
    const lines: string[] = [`# ${page.title}`, "", page.description, ""]
    for (const b of page.blocks) {
        switch (b.k) {
            case "h2": lines.push(`## ${b.text}`, ""); break
            case "h3": lines.push(`### ${b.text}`, ""); break
            case "p": lines.push(b.text, ""); break
            case "ul": lines.push(...b.items.map(i => `- ${i}`), ""); break
            case "ol": lines.push(...b.items.map((i, n) => `${n + 1}. ${i}`), ""); break
            case "callout": lines.push(`> ${b.title ? `**${b.title}** ` : ""}${b.text || ""}`, ...(b.items || []).map(i => `> - ${i}`), ""); break
            case "table": lines.push(`| ${b.headers.join(" | ")} |`, `| ${b.headers.map(() => "---").join(" | ")} |`, ...b.rows.map(r => `| ${r.join(" | ")} |`), ""); break
            case "code": lines.push("```", b.code, "```", ""); break
        }
    }
    return lines.join("\n")
}

export function DocsContent({ page, locale }: { page: DocPage; locale: string }) {
    const [copied, setCopied] = useState(false)
    const copy = async () => {
        try { await navigator.clipboard.writeText(toMarkdown(page)); setCopied(true); setTimeout(() => setCopied(false), 1600) } catch { /* ignore */ }
    }
    return (
        <article className="min-w-0">
            <p className="text-[13px] text-[#94A3B8]">{page.breadcrumb}</p>
            <div className="mt-2 flex items-start justify-between gap-4">
                <h1 className="text-[34px] font-bold leading-tight tracking-tight text-[#0F172A] dark:text-white">{page.title}</h1>
                <div className="hidden shrink-0 items-center rounded-lg border border-[#E5E7EB] dark:border-[#3b4248] sm:flex">
                    <button onClick={copy} className="flex items-center gap-1.5 px-3 py-1.5 text-[13px] font-medium text-[#475569] hover:text-[#0F172A] dark:text-[#c7d0da] dark:hover:text-white">
                        {copied ? <Check className="h-3.5 w-3.5 text-[#0F766E]" /> : <Copy className="h-3.5 w-3.5" />} {copied ? docsUi("copied", locale) : docsUi("copyPage", locale)}
                    </button>
                    <span className="border-l border-[#E5E7EB] px-2 py-1.5 text-[#94A3B8] dark:border-[#3b4248]"><ChevronDown className="h-3.5 w-3.5" /></span>
                </div>
            </div>
            <p className="mt-4 text-[17px] leading-8 text-[#64748B] dark:text-[#9aa7b4]">{page.description}</p>
            <div className="mt-8">
                <DocBlocks blocks={page.blocks} locale={locale} />
            </div>
        </article>
    )
}
