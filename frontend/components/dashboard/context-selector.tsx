"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { Building2, ChevronDown } from "lucide-react"

import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"


interface ContextAssignment {
    id: number
    school_id: number
    school_name: string
    organization_id: number
    organization_name?: string
    model_code: string
    model_name: string
    display_name: string
}

interface AcademicYear {
    id: number
    school_id: number
    school_model_assignment_id?: number
    name: string
    is_current: boolean
}

interface ContextOptions {
    assignments: ContextAssignment[]
    academic_years: AcademicYear[]
}

interface ActiveContext extends ContextAssignment {
    academic_year_id?: number
    academic_year_name?: string
}


export function ContextSelector() {
    const { token } = useAuth()
    const [options, setOptions] = useState<ContextOptions>({ assignments: [], academic_years: [] })
    const [active, setActive] = useState<ActiveContext | null>(null)
    const [open, setOpen] = useState(false)
    const [saving, setSaving] = useState(false)

    const load = useCallback(async () => {
        if (!token) return
        const headers = { Authorization: `Bearer ${token}` }
        const [optionsResponse, activeResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/context/options`, { headers }),
            fetch(`${API_BASE_URL}/context/active`, { headers }),
        ])
        if (optionsResponse.ok) setOptions(await optionsResponse.json())
        if (activeResponse.ok) {
            const row = await activeResponse.json() as ActiveContext
            setActive(row)
            localStorage.setItem("teducai_school_model_assignment_id", String(row.id))
            if (row.academic_year_id) localStorage.setItem("teducai_academic_year_id", String(row.academic_year_id))
        }
    }, [token])

    useEffect(() => {
        void load()
    }, [load])

    const availableYears = useMemo(
        () => options.academic_years.filter(year => year.school_model_assignment_id === active?.id || year.school_id === active?.school_id),
        [active?.id, active?.school_id, options.academic_years],
    )

    const update = async (assignmentId: number, academicYearId?: number) => {
        if (!token) return
        setSaving(true)
        try {
            const response = await fetch(`${API_BASE_URL}/context/active`, {
                method: "PUT",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({
                    school_model_assignment_id: assignmentId,
                    academic_year_id: academicYearId || null,
                }),
            })
            if (!response.ok) throw new Error("Impossible de changer de contexte")
            const row = await response.json() as ActiveContext
            localStorage.setItem("teducai_school_model_assignment_id", String(row.id))
            if (row.academic_year_id) localStorage.setItem("teducai_academic_year_id", String(row.academic_year_id))
            else localStorage.removeItem("teducai_academic_year_id")
            setActive(row)
            setOpen(false)
            window.dispatchEvent(new CustomEvent("teducai:context-changed", { detail: row }))
            window.location.reload()
        } finally {
            setSaving(false)
        }
    }

    if (!active) return null

    return (
        <div className="relative min-w-0">
            <button
                type="button"
                onClick={() => setOpen(previous => !previous)}
                className="flex max-w-[380px] items-center gap-2 rounded-xl px-2 py-1.5 text-left transition hover:bg-[#eef1f4] dark:hover:bg-[#343b41]"
                aria-expanded={open}
                title={`${active.organization_name} > ${active.school_name} > ${active.display_name} > ${active.academic_year_name || ""}`}
            >
                <Building2 className="h-4 w-4 shrink-0" />
                <span className="min-w-0">
                    <span className="block truncate text-sm font-bold">{active.school_name}</span>
                    <span className="block truncate text-xs text-[#667085] dark:text-[#b6c0cb]">
                        {active.organization_name} &gt; {active.display_name}{active.academic_year_name ? ` > ${active.academic_year_name}` : ""}
                    </span>
                </span>
                <ChevronDown className="h-4 w-4 shrink-0" />
            </button>
            {open && (
                <div className="absolute right-0 top-14 z-[1250] w-[min(420px,90vw)] rounded-[18px] border border-[#dfe3e8] bg-white p-3 shadow-[0_24px_80px_rgba(15,23,42,.22)] dark:border-[#3b4248] dark:bg-[#202528]">
                    <p className="px-2 pb-2 text-sm font-semibold">Contexte de travail</p>
                    <div className="max-h-[320px] space-y-1 overflow-y-auto">
                        {options.assignments.map(assignment => (
                            <button
                                key={assignment.id}
                                type="button"
                                disabled={saving}
                                onClick={() => void update(assignment.id)}
                                className={`block w-full rounded-xl px-3 py-2 text-left text-sm transition hover:bg-[#eef1f4] dark:hover:bg-[#343b41] ${assignment.id === active.id ? "bg-black text-white dark:bg-white dark:text-black" : ""}`}
                            >
                                <span className="block font-semibold">{assignment.school_name} - {assignment.display_name}</span>
                                <span className="block text-xs opacity-70">{assignment.organization_name}</span>
                            </button>
                        ))}
                    </div>
                    {availableYears.length > 0 && (
                        <label className="mt-3 block border-t border-[#e5e7eb] pt-3 text-xs dark:border-[#3b4248]">
                            Annee academique
                            <select
                                value={active.academic_year_id || ""}
                                onChange={event => void update(active.id, Number(event.target.value))}
                                className="mt-1 h-10 w-full rounded-xl border bg-transparent px-3 text-sm dark:border-[#4a535b]"
                            >
                                <option value="">Annee courante</option>
                                {availableYears.map(year => <option key={year.id} value={year.id}>{year.name}</option>)}
                            </select>
                        </label>
                    )}
                </div>
            )}
        </div>
    )
}
