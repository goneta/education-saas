"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Building2, ChevronDown, Search } from "lucide-react"
import { useTranslations } from "next-intl"

import { matchesText } from "@/lib/normalize"
import { useWorkingContext } from "@/contexts/working-context"


export function ContextSelector() {
    const t = useTranslations("layout")
    const { options, active, setContext } = useWorkingContext()
    const [open, setOpen] = useState(false)
    const [saving, setSaving] = useState(false)
    const [query, setQuery] = useState("")
    const cardRef = useRef<HTMLDivElement>(null)

    // Close on outside click / Escape.
    useEffect(() => {
        if (!open) return
        const onClick = (event: MouseEvent) => {
            if (cardRef.current && !cardRef.current.contains(event.target as Node)) setOpen(false)
        }
        const onKey = (event: KeyboardEvent) => {
            if (event.key === "Escape") setOpen(false)
        }
        document.addEventListener("mousedown", onClick)
        document.addEventListener("keydown", onKey)
        return () => {
            document.removeEventListener("mousedown", onClick)
            document.removeEventListener("keydown", onKey)
        }
    }, [open])

    // Search-as-you-type over the accessible institution/model assignments.
    const filteredAssignments = useMemo(() => {
        if (!query.trim()) return options.assignments
        return options.assignments.filter(
            assignment =>
                matchesText(assignment.school_name, query) ||
                matchesText(assignment.display_name, query) ||
                matchesText(assignment.model_name, query) ||
                matchesText(assignment.organization_name, query),
        )
    }, [options.assignments, query])

    const availableYears = useMemo(
        () =>
            options.academic_years.filter(
                year => year.school_model_assignment_id === active?.id || year.school_id === active?.school_id,
            ),
        [active?.id, active?.school_id, options.academic_years],
    )

    const apply = async (assignmentId: number, academicYearId?: number) => {
        setSaving(true)
        try {
            await setContext(assignmentId, academicYearId)
            setOpen(false)
        } finally {
            setSaving(false)
        }
    }

    // Nothing to select at all → don't render the control.
    if (!active && options.assignments.length === 0) return null

    return (
        <div className="relative min-w-0" ref={cardRef}>
            <button
                type="button"
                onClick={() => setOpen(previous => !previous)}
                className="flex max-w-[380px] items-center gap-2 rounded-xl px-2 py-1.5 text-left transition hover:bg-[#eef1f4] dark:hover:bg-[#343b41]"
                aria-expanded={open}
                title={active ? `${active.organization_name} > ${active.school_name} > ${active.display_name} > ${active.academic_year_name || ""}` : t("selectContext")}
            >
                <Building2 className="h-4 w-4 shrink-0" />
                {active ? (
                    <span className="min-w-0">
                        <span className="block truncate text-sm font-bold">{active.school_name}</span>
                        <span className="block truncate text-xs text-[#667085] dark:text-[#b6c0cb]">
                            {active.organization_name} &gt; {active.display_name}{active.academic_year_name ? ` > ${active.academic_year_name}` : ""}
                        </span>
                    </span>
                ) : (
                    <span className="truncate text-sm font-semibold text-[#667085] dark:text-[#b6c0cb]">{t("selectContext")}</span>
                )}
                <ChevronDown className="h-4 w-4 shrink-0" />
            </button>
            {open && (
                <div className="absolute right-0 top-14 z-[1250] w-[min(420px,90vw)] rounded-[18px] border border-[#dfe3e8] bg-white p-3 shadow-[0_24px_80px_rgba(15,23,42,.22)] dark:border-[#3b4248] dark:bg-[#202528]">
                    <p className="px-2 pb-2 text-sm font-semibold">{t("workingContext")}</p>
                    <div className="relative mb-2">
                        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9aa3ad]" />
                        <input
                            type="search"
                            autoFocus
                            value={query}
                            onChange={event => setQuery(event.target.value)}
                            placeholder={t("contextSearchPlaceholder")}
                            className="h-10 w-full rounded-xl border border-[#dfe3e8] bg-transparent pl-9 pr-3 text-sm outline-none focus:border-black dark:border-[#4a535b] dark:focus:border-white"
                        />
                    </div>
                    <div className="max-h-[320px] space-y-1 overflow-y-auto">
                        {filteredAssignments.length === 0 && (
                            <p className="px-3 py-4 text-center text-xs text-[#9aa3ad]">{t("contextNoResults")}</p>
                        )}
                        {filteredAssignments.map(assignment => (
                            <button
                                key={assignment.id}
                                type="button"
                                disabled={saving}
                                onClick={() => void apply(assignment.id)}
                                className={`block w-full rounded-xl px-3 py-2 text-left text-sm transition hover:bg-[#eef1f4] dark:hover:bg-[#343b41] ${assignment.id === active?.id ? "bg-black text-white dark:bg-white dark:text-black" : ""}`}
                            >
                                <span className="block font-semibold">{assignment.school_name} - {assignment.display_name}</span>
                                <span className="block text-xs opacity-70">{assignment.organization_name}</span>
                            </button>
                        ))}
                    </div>
                    {active && availableYears.length > 0 && (
                        <label className="mt-3 block border-t border-[#e5e7eb] pt-3 text-xs dark:border-[#3b4248]">
                            {t("academicYear")}
                            <select
                                value={active.academic_year_id || ""}
                                onChange={event => void apply(active.id, Number(event.target.value))}
                                className="mt-1 h-10 w-full rounded-xl border bg-transparent px-3 text-sm dark:border-[#4a535b]"
                            >
                                <option value="">{t("currentYear")}</option>
                                {availableYears.map(year => <option key={year.id} value={year.id}>{year.name}</option>)}
                            </select>
                        </label>
                    )}
                </div>
            )}
        </div>
    )
}
