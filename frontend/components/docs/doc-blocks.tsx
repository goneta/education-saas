"use client"

import { Fragment, type ReactNode } from "react"
import { Lightbulb, Info, AlertTriangle } from "lucide-react"

// A documentation page is a sequence of typed blocks. Inline markup inside text
// supports `code` (backtick → gray monospace pill) and [label](href) links.
export type DocBlock =
    | { k: "h2"; text: string }
    | { k: "h3"; text: string }
    | { k: "p"; text: string }
    | { k: "ul"; items: string[] }
    | { k: "ol"; items: string[] }
    | { k: "callout"; tone?: "tip" | "note" | "warn"; title?: string; text?: string; items?: string[] }
    | { k: "table"; headers: string[]; rows: string[][] }
    | { k: "code"; lang?: string; code: string }

export function slugify(text: string): string {
    return text.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
        .replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "")
}

// Minimal inline renderer: handles `code` spans, **bold** and [label](href) links.
// Internal links (starting with "/") are prefixed with the active locale.
export function Inline({ text, locale }: { text: string; locale?: string }): ReactNode {
    const tokens = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g).filter(Boolean)
    return tokens.map((tok, i) => {
        if (tok.startsWith("`") && tok.endsWith("`")) {
            return <code key={i} className="rounded-md bg-[#F1F3F5] px-1.5 py-0.5 font-mono text-[0.85em] text-[#475569] dark:bg-[#2a3035] dark:text-[#c7d0da]">{tok.slice(1, -1)}</code>
        }
        if (tok.startsWith("**") && tok.endsWith("**")) {
            return <strong key={i} className="font-semibold text-[#0F172A] dark:text-white">{tok.slice(2, -2)}</strong>
        }
        const link = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(tok)
        if (link) {
            let href = link[2]
            const external = /^https?:/.test(href) || href.startsWith("#")
            if (!external && href.startsWith("/") && locale && !href.startsWith(`/${locale}/`) && href !== `/${locale}`) {
                href = `/${locale}${href}`
            }
            return <a key={i} href={href} target={/^https?:/.test(link[2]) ? "_blank" : undefined} rel={/^https?:/.test(link[2]) ? "noreferrer" : undefined} className="text-[#0F766E] underline decoration-[#0F766E]/40 underline-offset-2 hover:decoration-[#0F766E] dark:text-[#5eead4]">{link[1]}</a>
        }
        return <Fragment key={i}>{tok}</Fragment>
    })
}

const CALLOUT = {
    tip: { Icon: Lightbulb, ring: "border-[#E5E7EB] bg-[#FAFBFC] dark:border-[#3b4248] dark:bg-[#1c2227]", icon: "text-[#0F766E]" },
    note: { Icon: Info, ring: "border-[#BFDBFE] bg-[#EFF6FF] dark:border-[#1e3a5f] dark:bg-[#13233a]", icon: "text-[#2563EB]" },
    warn: { Icon: AlertTriangle, ring: "border-[#FDE68A] bg-[#FFFBEB] dark:border-[#5a4a1e] dark:bg-[#2a2412]", icon: "text-[#B45309]" },
} as const

export function DocBlocks({ blocks, locale }: { blocks: DocBlock[]; locale?: string }) {
    return (
        <div className="space-y-5">
            {blocks.map((block, i) => {
                switch (block.k) {
                    case "h2":
                        return <h2 key={i} id={slugify(block.text)} className="scroll-mt-24 pt-4 text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white">{block.text}</h2>
                    case "h3":
                        return <h3 key={i} id={slugify(block.text)} className="scroll-mt-24 pt-2 text-lg font-semibold text-[#0F172A] dark:text-white">{block.text}</h3>
                    case "p":
                        return <p key={i} className="text-[15px] leading-7 text-[#374151] dark:text-[#c7d0da]"><Inline locale={locale} text={block.text} /></p>
                    case "ul":
                        return <ul key={i} className="ml-1 space-y-1.5">{block.items.map((it, j) => <li key={j} className="flex gap-2.5 text-[15px] leading-7 text-[#374151] dark:text-[#c7d0da]"><span className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#0F766E]" /><span><Inline locale={locale} text={it} /></span></li>)}</ul>
                    case "ol":
                        return <ol key={i} className="ml-1 space-y-1.5">{block.items.map((it, j) => <li key={j} className="flex gap-2.5 text-[15px] leading-7 text-[#374151] dark:text-[#c7d0da]"><span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#0F766E]/10 text-xs font-semibold text-[#0F766E]">{j + 1}</span><span><Inline locale={locale} text={it} /></span></li>)}</ol>
                    case "callout": {
                        const tone = CALLOUT[block.tone || "tip"]
                        const Icon = tone.Icon
                        return (
                            <div key={i} className={`flex gap-3 rounded-xl border px-4 py-3.5 ${tone.ring}`}>
                                <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${tone.icon}`} />
                                <div className="space-y-1.5 text-[15px] leading-7 text-[#374151] dark:text-[#c7d0da]">
                                    {block.title && <p className="font-semibold text-[#0F172A] dark:text-white">{block.title}</p>}
                                    {block.text && <p><Inline locale={locale} text={block.text} /></p>}
                                    {block.items && <ul className="space-y-1">{block.items.map((it, j) => <li key={j} className="flex gap-2"><span className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-current opacity-50" /><span><Inline locale={locale} text={it} /></span></li>)}</ul>}
                                </div>
                            </div>
                        )
                    }
                    case "table":
                        return (
                            <div key={i} className="overflow-x-auto rounded-xl border border-[#E5E7EB] dark:border-[#3b4248]">
                                <table className="w-full text-left text-[14px]">
                                    <thead><tr className="border-b border-[#E5E7EB] dark:border-[#3b4248]">{block.headers.map((h, j) => <th key={j} className="px-4 py-3 font-semibold text-[#0F172A] dark:text-white">{h}</th>)}</tr></thead>
                                    <tbody>{block.rows.map((row, r) => <tr key={r} className="border-b border-[#F0F1F3] last:border-0 dark:border-[#2a3035]">{row.map((cell, c) => <td key={c} className="px-4 py-3 align-top text-[#374151] dark:text-[#c7d0da]"><Inline locale={locale} text={cell} /></td>)}</tr>)}</tbody>
                                </table>
                            </div>
                        )
                    case "code":
                        return <pre key={i} className="overflow-x-auto rounded-xl border border-[#E5E7EB] bg-[#FAFBFC] p-4 text-[13px] leading-6 dark:border-[#3b4248] dark:bg-[#15191d]"><code className="font-mono text-[#334155] dark:text-[#c7d0da]">{block.code}</code></pre>
                    default:
                        return null
                }
            })}
        </div>
    )
}
