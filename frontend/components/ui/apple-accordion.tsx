"use client"

import type { ReactNode } from "react"
import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface AppleAccordionProps {
    title: string
    open: boolean
    onToggle: () => void
    children: ReactNode
    hint?: string
    lazy?: boolean
}

export function AppleAccordion({
    title,
    open,
    onToggle,
    children,
    hint = "Cliquez pour afficher le contenu",
    lazy = false,
}: AppleAccordionProps) {
    return (
        <section className={cn(
            "overflow-hidden rounded-[24px] border border-[#E5E7EB] bg-white shadow-sm transition-colors duration-300",
            open && "bg-[#FBFBFD]"
        )}>
            <button
                type="button"
                onClick={onToggle}
                aria-expanded={open}
                className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition hover:bg-[#F5F5F7]"
                title={open ? "Cliquez pour refermer cette section" : hint}
            >
                <span>
                    <span className="block text-lg font-semibold text-[#111827]">{title}</span>
                    {!open && <span className="mt-1 block text-sm font-normal text-[#6B7280]">{hint}</span>}
                </span>
                <ChevronDown className={cn("h-5 w-5 shrink-0 text-[#6B7280] transition-transform duration-300", open && "rotate-180")} />
            </button>
            <div className={cn(
                "grid transition-[grid-template-rows,opacity] duration-300 ease-out",
                open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
            )}>
                <div className="overflow-hidden">
                    {(!lazy || open) && <div className="px-5 pb-5 pt-1">{children}</div>}
                </div>
            </div>
        </section>
    )
}
