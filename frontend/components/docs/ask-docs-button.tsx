"use client"

import { useState } from "react"
import { BookOpen, X, Sparkles } from "lucide-react"

// Floating "Ask TeducAI" helper. The panel is a placeholder ready to be wired to
// the AI search assistant; for now it routes the user to the chat agent.
export function AskDocsButton({ locale }: { locale: string }) {
    const [open, setOpen] = useState(false)
    return (
        <>
            {open && (
                <div className="fixed bottom-24 right-6 z-50 w-[min(92vw,360px)] rounded-2xl border border-[#E5E7EB] bg-white p-4 shadow-xl dark:border-[#3b4248] dark:bg-[#1c2227]">
                    <div className="mb-2 flex items-center justify-between">
                        <p className="flex items-center gap-2 text-sm font-semibold text-[#0F172A] dark:text-white"><Sparkles className="h-4 w-4 text-[#0F766E]" /> Ask TeducAI</p>
                        <button onClick={() => setOpen(false)} aria-label="Close"><X className="h-4 w-4 text-[#94A3B8]" /></button>
                    </div>
                    <p className="text-sm text-[#64748B] dark:text-[#c7d0da]">Ask a question about TeducAI and get an answer grounded in these docs. The AI assistant lives in your dashboard.</p>
                    <a href={`/${locale}/dashboard/ai-command-center`} className="mt-3 block rounded-xl bg-[#0F766E] px-4 py-2 text-center text-sm font-medium text-white hover:bg-[#0F766E]/90">Open the AI assistant</a>
                </div>
            )}
            <button onClick={() => setOpen(v => !v)}
                className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-[#0F172A] px-5 py-3 text-sm font-medium text-white shadow-lg hover:bg-[#0F172A]/90 dark:bg-white dark:text-[#0F172A] dark:hover:bg-white/90">
                <BookOpen className="h-4 w-4" /> Ask TeducAI
            </button>
        </>
    )
}
