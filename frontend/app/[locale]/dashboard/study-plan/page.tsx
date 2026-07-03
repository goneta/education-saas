"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { BookOpenCheck, CalendarDays, ClipboardList, GraduationCap } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface Child { student_id: number; full_name?: string | null; registration_number?: string | null }
interface AssessmentItem { id: number; title: string; subject?: string | null; date: string; type?: string | null; max_score?: number | null }
interface HomeworkItem { id: number; title: string; subject?: string | null; due_date: string }
interface RevisionSlot { date: string; subject?: string | null; assessment_title: string; assessment_date: string; step: string; duration_minutes: number }
interface Plan { assessments: AssessmentItem[]; homework: HomeworkItem[]; revision_slots: RevisionSlot[] }

export default function StudyPlanPage() {
    const t = useTranslations("studyPlan")
    const { token, user } = useAuth()
    const [children, setChildren] = useState<Child[]>([])
    const [studentId, setStudentId] = useState<number | null>(null)
    const [plan, setPlan] = useState<Plan | null>(null)
    const [error, setError] = useState<string | null>(null)

    const isParent = String(user?.role || "").toLowerCase() === "parent"
    const headers = useMemo(() => token ? { Authorization: `Bearer ${token}` } : undefined, [token])

    useEffect(() => {
        if (!headers || !isParent) return
        void (async () => {
            const res = await fetch(`${API_BASE_URL}/self-documents/children`, { headers })
            if (res.ok) {
                const rows: Child[] = await res.json()
                setChildren(rows)
                if (rows.length) setStudentId(rows[0].student_id)
            }
        })()
    }, [headers, isParent])

    const loadPlan = useCallback(async () => {
        if (!headers || (isParent && studentId === null)) return
        setError(null)
        const qs = isParent && studentId ? `?student_id=${studentId}` : ""
        const res = await fetch(`${API_BASE_URL}/automations/study-plan${qs}`, { headers })
        if (res.ok) setPlan(await res.json())
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }, [headers, isParent, studentId])

    useEffect(() => { void loadPlan() }, [loadPlan])

    const stepLabel = (step: string) => step === "final_review" ? t("stepFinal") : step === "practice" ? t("stepPractice") : t("stepOverview")
    const stepColor = (step: string) => step === "final_review" ? "bg-red-100 text-red-800" : step === "practice" ? "bg-amber-100 text-amber-800" : "bg-blue-100 text-blue-800"

    const slotsByDay = useMemo(() => {
        const groups: Record<string, RevisionSlot[]> = {}
        for (const slot of plan?.revision_slots || []) {
            const key = new Date(slot.date).toLocaleDateString()
            groups[key] = groups[key] || []
            groups[key].push(slot)
        }
        return Object.entries(groups)
    }, [plan])

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            {isParent && children.length > 1 && (
                <div className="max-w-sm">
                    <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("selectChild")}
                        <select value={studentId ?? ""} onChange={e => setStudentId(Number(e.target.value))} className="apple-select mt-1 w-full">
                            {children.map(c => <option key={c.student_id} value={c.student_id}>{c.full_name || c.registration_number || `#${c.student_id}`}</option>)}
                        </select>
                    </label>
                </div>
            )}

            <div className="grid gap-4 lg:grid-cols-2">
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2"><GraduationCap className="h-4 w-4" /> {t("assessments")}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {(plan?.assessments || []).length === 0 ? <p className="py-4 text-center text-sm text-[#6B7280]">{t("noAssessments")}</p> : (
                            <ul className="space-y-2">
                                {plan!.assessments.map(a => (
                                    <li key={a.id} className="flex items-center justify-between rounded-lg border border-[#F0F1F3] px-3 py-2 dark:border-[#2a3035]">
                                        <span><span className="font-medium">{a.title}</span>{a.subject && <span className="ml-2 text-sm text-[#6B7280]">{a.subject}</span>}</span>
                                        <span className="text-sm text-[#6B7280]">{new Date(a.date).toLocaleDateString()}</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </CardContent>
                </Card>

                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2"><ClipboardList className="h-4 w-4" /> {t("homework")}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {(plan?.homework || []).length === 0 ? <p className="py-4 text-center text-sm text-[#6B7280]">{t("noHomework")}</p> : (
                            <ul className="space-y-2">
                                {plan!.homework.map(h => (
                                    <li key={h.id} className="flex items-center justify-between rounded-lg border border-[#F0F1F3] px-3 py-2 dark:border-[#2a3035]">
                                        <span><span className="font-medium">{h.title}</span>{h.subject && <span className="ml-2 text-sm text-[#6B7280]">{h.subject}</span>}</span>
                                        <span className="text-sm text-[#6B7280]">{t("due")} {new Date(h.due_date).toLocaleDateString()}</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </CardContent>
                </Card>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><CalendarDays className="h-4 w-4" /> {t("revisionSchedule")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("revisionHint")}</p>
                </CardHeader>
                <CardContent>
                    {slotsByDay.length === 0 ? <p className="py-4 text-center text-sm text-[#6B7280]">{t("noSlots")}</p> : (
                        <div className="space-y-4">
                            {slotsByDay.map(([day, slots]) => (
                                <div key={day}>
                                    <p className="mb-2 text-sm font-semibold text-[#111827] dark:text-white">{day}</p>
                                    <ul className="space-y-2">
                                        {slots.map((slot, index) => (
                                            <li key={`${day}-${index}`} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[#F0F1F3] px-3 py-2 dark:border-[#2a3035]">
                                                <span className="flex items-center gap-2">
                                                    <BookOpenCheck className="h-4 w-4 text-[#6B7280]" />
                                                    <span className="font-medium">{slot.subject || "—"}</span>
                                                    <span className="text-sm text-[#6B7280]">{slot.assessment_title}</span>
                                                </span>
                                                <span className="flex items-center gap-2 text-sm">
                                                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${stepColor(slot.step)}`}>{stepLabel(slot.step)}</span>
                                                    <span className="text-[#6B7280]">{slot.duration_minutes} min</span>
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
