"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useTranslations } from "next-intl"
import { Camera, Check, RefreshCw, ScanLine } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface AssessmentRow { id: number; title: string; subject?: string | null; class_name?: string | null; date: string; max_score: number; grades: number }
interface Proposal { student_id: number; student_name?: string | null; extracted_name: string; score: number; confidence: number; existing_score?: number | null; out_of_range: boolean }
interface UnmatchedEntry { name: string; score: number }
interface MissingStudent { student_id: number; student_name?: string | null }
interface ScanResult { assessment_id: number; assessment_title: string; class_name?: string | null; max_score: number; model_name?: string | null; proposals: Proposal[]; unmatched: UnmatchedEntry[]; missing_students: MissingStudent[] }

export default function GradeScanPage() {
    const t = useTranslations("gradeOcr")
    const { token } = useAuth()
    const fileInputRef = useRef<HTMLInputElement>(null)
    const [assessments, setAssessments] = useState<AssessmentRow[]>([])
    const [assessmentId, setAssessmentId] = useState("")
    const [scan, setScan] = useState<ScanResult | null>(null)
    const [scores, setScores] = useState<Record<number, string>>({})
    const [busy, setBusy] = useState<"scan" | "confirm" | null>(null)
    const [saved, setSaved] = useState<{ created: number; updated: number } | null>(null)
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { Authorization: `Bearer ${token}` } : undefined, [token])

    const loadAssessments = useCallback(async () => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/automations/remediation/assessments?limit=30`, { headers })
        if (res.ok) {
            const rows: AssessmentRow[] = await res.json()
            setAssessments(rows)
            if (rows.length && !assessmentId) setAssessmentId(String(rows[0].id))
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [headers])

    useEffect(() => { void loadAssessments() }, [loadAssessments])

    const runScan = async (file: File) => {
        if (!headers || !assessmentId) return
        setBusy("scan"); setError(null); setScan(null); setSaved(null)
        try {
            const body = new FormData()
            body.append("photo", file)
            const res = await fetch(`${API_BASE_URL}/automations/grade-ocr/${assessmentId}/scan`, { method: "POST", headers, body })
            const data = await res.json().catch(() => null)
            if (!res.ok) { setError(data?.detail || "—"); return }
            setScan(data)
            const initial: Record<number, string> = {}
            for (const proposal of data.proposals) initial[proposal.student_id] = String(proposal.score)
            setScores(initial)
        } finally {
            setBusy(null)
        }
    }

    const confirm = async () => {
        if (!headers || !scan) return
        const entries = Object.entries(scores)
            .filter(([, value]) => value !== "" && !Number.isNaN(Number(value)))
            .map(([studentId, value]) => ({ student_id: Number(studentId), score: Number(value) }))
        if (!entries.length) return
        setBusy("confirm"); setError(null)
        try {
            const res = await fetch(`${API_BASE_URL}/automations/grade-ocr/${scan.assessment_id}/confirm`, {
                method: "POST",
                headers: { ...headers, "Content-Type": "application/json" },
                body: JSON.stringify({ entries }),
            })
            const data = await res.json().catch(() => null)
            if (!res.ok) { setError(data?.detail || "—"); return }
            setSaved(data)
            setScan(null)
            void loadAssessments()
        } finally {
            setBusy(null)
        }
    }

    const confidenceBadge = (confidence: number) => (
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${confidence >= 0.85 ? "bg-emerald-100 text-emerald-800" : confidence >= 0.7 ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800"}`}>
            {Math.round(confidence * 100)}%
        </span>
    )

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}
            {saved && (
                <div className="rounded-xl border border-[#CCFBF1] bg-[#F0FDFA] px-3 py-2 text-sm text-[#0F766E] dark:border-[#134E4A] dark:bg-[#0f1f1d] dark:text-[#5eead4]">
                    {t("savedSummary", { created: saved.created, updated: saved.updated })}
                </div>
            )}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><ScanLine className="h-4 w-4" /> {t("scanTitle")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("scanHint")}</p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-3 md:grid-cols-3">
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da] md:col-span-2">{t("assessment")}
                            <select value={assessmentId} onChange={e => setAssessmentId(e.target.value)} className="apple-select mt-1 w-full">
                                {assessments.length === 0 && <option value="">{t("noAssessments")}</option>}
                                {assessments.map(row => (
                                    <option key={row.id} value={row.id}>{row.title} — {row.subject} — {row.class_name} ({new Date(row.date).toLocaleDateString()})</option>
                                ))}
                            </select>
                        </label>
                        <div className="flex items-end">
                            <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" capture="environment" className="hidden" onChange={e => {
                                const file = e.target.files?.[0]
                                if (file) void runScan(file)
                                e.currentTarget.value = ""
                            }} />
                            <Button onClick={() => fileInputRef.current?.click()} disabled={busy !== null || !assessmentId} className="w-full bg-black text-white hover:bg-black/90">
                                {busy === "scan" ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Camera className="mr-2 h-4 w-4" />}
                                {busy === "scan" ? t("scanning") : t("takePhoto")}
                            </Button>
                        </div>
                    </div>
                    <p className="text-xs text-[#94A3B8]">{t("providerHint")}</p>
                </CardContent>
            </Card>

            {scan && (
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader>
                        <CardTitle>{scan.assessment_title} — {scan.class_name}</CardTitle>
                        <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("reviewHint", { max: scan.max_score, model: scan.model_name || "—" })}</p>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("student")}</th><th className="px-3 py-2">{t("extractedName")}</th><th className="px-3 py-2">{t("confidence")}</th><th className="px-3 py-2">{t("existing")}</th><th className="px-3 py-2">{t("score")}</th></tr></thead>
                                <tbody>
                                    {scan.proposals.length === 0 ? <tr><td colSpan={5} className="px-3 py-6 text-center text-[#6B7280]">{t("noProposals")}</td></tr> : scan.proposals.map(proposal => (
                                        <tr key={proposal.student_id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                            <td className="px-3 py-2 font-medium">{proposal.student_name}</td>
                                            <td className="px-3 py-2 text-[#6B7280]">{proposal.extracted_name}</td>
                                            <td className="px-3 py-2">{confidenceBadge(proposal.confidence)}</td>
                                            <td className="px-3 py-2">{proposal.existing_score ?? "—"}</td>
                                            <td className="px-3 py-2">
                                                <input type="number" min={0} max={scan.max_score} step="0.5" value={scores[proposal.student_id] ?? ""}
                                                    onChange={e => setScores({ ...scores, [proposal.student_id]: e.target.value })}
                                                    className={`apple-input w-24 ${proposal.out_of_range ? "border-red-400" : ""}`} />
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {scan.unmatched.length > 0 && (
                            <p className="text-sm text-[#B45309] dark:text-[#fcd34d]">{t("unmatched")}: {scan.unmatched.map(u => `${u.name} (${u.score})`).join(", ")}</p>
                        )}
                        {scan.missing_students.length > 0 && (
                            <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("missing")}: {scan.missing_students.map(m => m.student_name).join(", ")}</p>
                        )}

                        <Button onClick={confirm} disabled={busy !== null || scan.proposals.length === 0} className="bg-black text-white hover:bg-black/90">
                            {busy === "confirm" ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Check className="mr-2 h-4 w-4" />}
                            {t("confirm")}
                        </Button>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
