"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"

import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"

export interface ContextAssignment {
    id: number
    school_id: number
    school_name: string
    organization_id: number
    organization_name?: string
    model_code: string
    model_name: string
    display_name: string
}

export interface AcademicYear {
    id: number
    school_id: number
    school_model_assignment_id?: number
    name: string
    is_current: boolean
}

export interface ContextOptions {
    assignments: ContextAssignment[]
    academic_years: AcademicYear[]
}

export interface ActiveContext extends ContextAssignment {
    academic_year_id?: number
    academic_year_name?: string
}

interface WorkingContextValue {
    options: ContextOptions
    active: ActiveContext | null
    loading: boolean
    /** True once the active-context fetch has resolved (success or not). */
    ready: boolean
    refresh: () => Promise<void>
    /** Persist a new working context (institution+model, optional year) globally. */
    setContext: (assignmentId: number, academicYearId?: number | null) => Promise<void>
}

const WorkingContext = createContext<WorkingContextValue | null>(null)

export function WorkingContextProvider({ children }: { children: React.ReactNode }) {
    const { token } = useAuth()
    const [options, setOptions] = useState<ContextOptions>({ assignments: [], academic_years: [] })
    const [active, setActive] = useState<ActiveContext | null>(null)
    const [loading, setLoading] = useState(true)
    const [ready, setReady] = useState(false)

    const persistLocal = useCallback((row: ActiveContext | null) => {
        if (!row) return
        localStorage.setItem("teducai_school_model_assignment_id", String(row.id))
        if (row.academic_year_id) localStorage.setItem("teducai_academic_year_id", String(row.academic_year_id))
        else localStorage.removeItem("teducai_academic_year_id")
    }, [])

    const refresh = useCallback(async () => {
        if (!token) {
            setActive(null)
            setLoading(false)
            setReady(true)
            return
        }
        setLoading(true)
        const headers = { Authorization: `Bearer ${token}` }
        try {
            const [optionsResponse, activeResponse] = await Promise.all([
                fetch(`${API_BASE_URL}/context/options`, { headers }),
                fetch(`${API_BASE_URL}/context/active`, { headers }),
            ])
            if (optionsResponse.ok) setOptions(await optionsResponse.json())
            if (activeResponse.ok) {
                const row = (await activeResponse.json()) as ActiveContext
                setActive(row)
                persistLocal(row)
            } else {
                // 400/403 → no active institution/model/year resolved for this user.
                setActive(null)
            }
        } catch {
            setActive(null)
        } finally {
            setLoading(false)
            setReady(true)
        }
    }, [token, persistLocal])

    useEffect(() => {
        void refresh()
    }, [refresh])

    const setContext = useCallback(
        async (assignmentId: number, academicYearId?: number | null) => {
            if (!token) return
            const response = await fetch(`${API_BASE_URL}/context/active`, {
                method: "PUT",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({
                    school_model_assignment_id: assignmentId,
                    academic_year_id: academicYearId || null,
                }),
            })
            if (!response.ok) throw new Error("Impossible de changer de contexte")
            const row = (await response.json()) as ActiveContext
            setActive(row)
            persistLocal(row)
            window.dispatchEvent(new CustomEvent("teducai:context-changed", { detail: row }))
            // Reload so every already-mounted module re-fetches its data under the
            // newly active institution/model/year context.
            window.location.reload()
        },
        [token, persistLocal],
    )

    const value = useMemo<WorkingContextValue>(
        () => ({ options, active, loading, ready, refresh, setContext }),
        [options, active, loading, ready, refresh, setContext],
    )

    return <WorkingContext.Provider value={value}>{children}</WorkingContext.Provider>
}

export function useWorkingContext(): WorkingContextValue {
    const value = useContext(WorkingContext)
    if (!value) throw new Error("useWorkingContext must be used within a WorkingContextProvider")
    return value
}
