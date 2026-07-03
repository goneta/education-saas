"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { Sparkles, RefreshCw, Wand2 } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface AssessmentRow { id: number; title: string; subject?: string | null; class_name?: string | null; date: string; max_score: number; grades: number; average?: number | null; struggling: number }
interface GeneratedSet { student_id: number; student_name?: string | null; score: number; practice_set: string }
interface RunSummary { assessment_id: number; assessment_title: string; graded: number; generated: GeneratedSet[]; skipped_done: number; above_threshold: number }

export default function RemediationPage() {
    const t = useTranslations("remediation")
    const { token } = useAuth()
    const [rows, setRows] = useState<AssessmentRow[]>([])
    const [threshold, setThreshold] = useState("50")
    const [busyId, setBusyId] = useState<number | null>(null)
    const [summary, setSummary] = useState<RunSummary | null>(null)
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/automations/remediation/assessments?limit=30`, { headers })
        if (res.ok) setRows(await res.json())
    }, [headers])

    useEffect(() => { void load() }, [load])

    const run = async (assessmentId: number) => {
        if (!headers) return
        setBusyId(assessmentId); setError(null); setSummary(null)
        try {
            const ratio = Math.min(Math.max(Number(threshold) || 50, 1), 100) / 100
            const res = await fetch(`${API_BASE_URL}/automations/remediation/${assessmentId}/run?threshold_ratio=${ratio}`, { method: "POST", headers })
            if (res.ok) { setSummary(await res.json()); void load() }
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

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><Wand2 className="h-4 w-4" /> {t("assessments")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("assessmentsHint")}</p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <label className="block max-w-xs text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("threshold")}
                        <input type="number" min={1} max={100} value={threshold} onChange={e => setThreshold(e.target.value)} className="apple-input mt-1 w-full" />
                    </label>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("assessment")}</th><th className="px-3 py-2">{t("subject")}</th><th className="px-3 py-2">{t("class")}</th><th className="px-3 py-2">{t("date")}</th><th className="px-3 py-2">{t("gradesCol")}</th><th className="px-3 py-2">{t("average")}</th><th className="px-3 py-2">{t("struggling")}</th><th className="px-3 py-2"></th></tr></thead>
                            <tbody>
                                {rows.length === 0 ? <tr><td colSpan={8} className="px-3 py-6 text-center text-[#6B7280]">{t("noAssessments")}</td></tr> : rows.map(row => (
                                    <tr key={row.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                        <td className="px-3 py-2 font-medium">{row.title}</td>
                                        <td className="px-3 py-2">{row.subject || "—"}</td>
                                        <td className="px-3 py-2">{row.class_name || "—"}</td>
                                        <td className="px-3 py-2">{new Date(row.date).toLocaleDateString()}</td>
                                        <td className="px-3 py-2">{row.grades}</td>
                                        <td className="px-3 py-2">{row.average ?? "—"}{row.average != null && `/${row.max_score}`}</td>
                                        <td className="px-3 py-2">
                                            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${row.struggling > 0 ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800"}`}>{row.struggling}</span>
                                        </td>
                                        <td className="px-3 py-2 text-right">
                                            <Button size="sm" onClick={() => run(row.id)} disabled={busyId !== null || row.grades === 0} className="bg-black text-white hover:bg-black/90">
                                                {busyId === row.id ? <RefreshCw className="mr-1 h-3 w-3 animate-spin" /> : <Sparkles className="mr-1 h-3 w-3" />}
                                                {t("generate")}
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            {summary && (
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader>
                        <CardTitle>{t("resultTitle", { title: summary.assessment_title })}</CardTitle>
                        <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("resultHint", { generated: summary.generated.length, skipped: summary.skipped_done, above: summary.above_threshold })}</p>
                    </CardHeader>
                    <CardContent>
                        {summary.generated.length === 0 ? <p className="py-4 text-center text-sm text-[#6B7280]">{t("nothingToGenerate")}</p> : (
                            <div className="space-y-2">
                                {summary.generated.map(item => (
                                    <details key={item.student_id} className="rounded-xl border border-[#E5E7EB] px-3 py-2 dark:border-[#3b4248]">
                                        <summary className="cursor-pointer text-sm font-medium text-[#111827] dark:text-white">
                                            {item.student_name || `#${item.student_id}`} <span className="ml-2 text-xs font-normal text-[#6B7280]">{t("score")} {item.score}</span>
                                        </summary>
                                        <pre className="mt-2 whitespace-pre-wrap font-sans text-sm text-[#374151] dark:text-[#c7d0da]">{item.practice_set}</pre>
                                    </details>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
