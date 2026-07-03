"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useLocale, useTranslations } from "next-intl"
import { Lightbulb, RefreshCw, Sparkles } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface Child { student_id: number; full_name?: string | null; registration_number?: string | null }
interface GradeRow { grade_id: number; assessment_title: string; subject?: string | null; date: string; score: number; max_score: number; class_average?: number | null; class_best?: number | null; class_size: number; comment?: string | null }
interface Explanation { grade_id: number; assessment_title: string; subject?: string | null; score: number; max_score: number; class_average?: number | null; class_best?: number | null; rank?: number | null; class_size: number; explanation: string }

export default function ExplainGradePage() {
    const t = useTranslations("explainGrade")
    const locale = useLocale()
    const { token, user } = useAuth()
    const [children, setChildren] = useState<Child[]>([])
    const [studentId, setStudentId] = useState<number | null>(null)
    const [grades, setGrades] = useState<GradeRow[]>([])
    const [busyId, setBusyId] = useState<number | null>(null)
    const [explanation, setExplanation] = useState<Explanation | null>(null)
    const [error, setError] = useState<string | null>(null)

    const isParent = String(user?.role || "").toLowerCase() === "parent"
    const headers = useMemo(() => token ? { Authorization: `Bearer ${token}` } : undefined, [token])
    const sidQs = isParent && studentId ? `student_id=${studentId}&` : ""

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

    const loadGrades = useCallback(async () => {
        if (!headers || (isParent && studentId === null)) return
        setError(null)
        const res = await fetch(`${API_BASE_URL}/automations/explain-grade/grades?${sidQs}limit=20`, { headers })
        if (res.ok) setGrades(await res.json())
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }, [headers, isParent, studentId, sidQs])

    useEffect(() => { void loadGrades() }, [loadGrades])

    const explain = async (gradeId: number) => {
        if (!headers) return
        setBusyId(gradeId); setError(null); setExplanation(null)
        try {
            const res = await fetch(`${API_BASE_URL}/automations/explain-grade/${gradeId}/run?${sidQs}language=${locale}`, { method: "POST", headers })
            if (res.ok) setExplanation(await res.json())
            else setError((await res.json().catch(() => ({}))).detail || "—")
        } finally {
            setBusyId(null)
        }
    }

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

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><Lightbulb className="h-4 w-4" /> {t("myGrades")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("myGradesHint")}</p>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("assessment")}</th><th className="px-3 py-2">{t("subject")}</th><th className="px-3 py-2">{t("date")}</th><th className="px-3 py-2">{t("score")}</th><th className="px-3 py-2">{t("classAverage")}</th><th className="px-3 py-2"></th></tr></thead>
                            <tbody>
                                {grades.length === 0 ? <tr><td colSpan={6} className="px-3 py-6 text-center text-[#6B7280]">{t("noGrades")}</td></tr> : grades.map(row => (
                                    <tr key={row.grade_id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                        <td className="px-3 py-2 font-medium">{row.assessment_title}</td>
                                        <td className="px-3 py-2">{row.subject || "—"}</td>
                                        <td className="px-3 py-2">{new Date(row.date).toLocaleDateString()}</td>
                                        <td className="px-3 py-2">
                                            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${row.score < 0.5 * row.max_score ? "bg-red-100 text-red-800" : "bg-emerald-100 text-emerald-800"}`}>{row.score}/{row.max_score}</span>
                                        </td>
                                        <td className="px-3 py-2">{row.class_average ?? "—"}</td>
                                        <td className="px-3 py-2 text-right">
                                            <Button size="sm" onClick={() => explain(row.grade_id)} disabled={busyId !== null} className="bg-black text-white hover:bg-black/90">
                                                {busyId === row.grade_id ? <RefreshCw className="mr-1 h-3 w-3 animate-spin" /> : <Sparkles className="mr-1 h-3 w-3" />}
                                                {t("explain")}
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            {explanation && (
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader>
                        <CardTitle>{explanation.assessment_title}{explanation.subject && <span className="ml-2 text-sm font-normal text-[#6B7280]">{explanation.subject}</span>}</CardTitle>
                        <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">
                            {t("statsLine", {
                                score: `${explanation.score}/${explanation.max_score}`,
                                average: String(explanation.class_average ?? "—"),
                                rank: String(explanation.rank ?? "—"),
                                size: String(explanation.class_size),
                            })}
                        </p>
                    </CardHeader>
                    <CardContent>
                        <pre className="whitespace-pre-wrap font-sans text-sm text-[#374151] dark:text-[#c7d0da]">{explanation.explanation}</pre>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
