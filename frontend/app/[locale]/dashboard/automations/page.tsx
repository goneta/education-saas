"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { AlertTriangle, BellRing, Mail, Play, RefreshCw, UserX } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface RunResult { scanned: number; reminded: number; escalated: number; skipped_cooldown: number; skipped_not_due: number; skipped_paid: number; sms_queued: number }
interface Reminder { id: number; fee_id: number; fee_title?: string | null; student_name?: string | null; level: number; outstanding_amount: number; channels: string[]; created_at: string }
interface DigestResult { links: number; digests: number; grade_alerts: number; absence_alerts: number; skipped_cooldown: number }
interface DigestNotification { id: number; event_type: string; recipient_name?: string | null; subject?: string | null; message: string; created_at: string }
interface FollowupResult { scanned: number; notified: number; sms_queued: number; skipped_done: number; skipped_no_contact: number }
interface AnomalyResult { skipped_cooldown: boolean; anomalies: number; notified: number; absences_current?: number | null; absences_previous?: number | null; unpaid_ratio?: number | null; class_size_min?: number | null; class_size_max?: number | null }

export default function AutomationsPage() {
    const t = useTranslations("automations")
    const { token } = useAuth()
    const [params, setParams] = useState({ level2_days: "15", level3_days: "30", cooldown_days: "3" })
    const [running, setRunning] = useState(false)
    const [result, setResult] = useState<RunResult | null>(null)
    const [history, setHistory] = useState<Reminder[]>([])
    const [error, setError] = useState<string | null>(null)
    const [digestParams, setDigestParams] = useState({ days: "7", grade_alert_threshold: "10", absence_alert_count: "3" })
    const [digestRunning, setDigestRunning] = useState(false)
    const [digestResult, setDigestResult] = useState<DigestResult | null>(null)
    const [digestHistory, setDigestHistory] = useState<DigestNotification[]>([])
    const [followupDays, setFollowupDays] = useState("2")
    const [followupRunning, setFollowupRunning] = useState(false)
    const [followupResult, setFollowupResult] = useState<FollowupResult | null>(null)
    const [followupHistory, setFollowupHistory] = useState<DigestNotification[]>([])
    const [anomalyParams, setAnomalyParams] = useState({ days: "7", unpaid_threshold: "30" })
    const [anomalyRunning, setAnomalyRunning] = useState(false)
    const [anomalyResult, setAnomalyResult] = useState<AnomalyResult | null>(null)
    const [anomalyHistory, setAnomalyHistory] = useState<DigestNotification[]>([])

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const loadHistory = useCallback(async () => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/automations/fee-reminders/history?limit=50`, { headers })
        if (res.ok) setHistory(await res.json())
    }, [headers])

    const loadDigestHistory = useCallback(async () => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/automations/parent-digest/history?limit=50`, { headers })
        if (res.ok) setDigestHistory(await res.json())
    }, [headers])

    const loadEventHistory = useCallback(async (eventType: string, setter: (rows: DigestNotification[]) => void) => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/automations/notifications/history?event_type=${eventType}&limit=50`, { headers })
        if (res.ok) setter(await res.json())
    }, [headers])

    useEffect(() => {
        void loadHistory(); void loadDigestHistory()
        void loadEventHistory("absence.followup", setFollowupHistory)
        void loadEventHistory("anomaly.digest", setAnomalyHistory)
    }, [loadHistory, loadDigestHistory, loadEventHistory])

    const run = async () => {
        if (!headers) return
        setRunning(true); setError(null); setResult(null)
        try {
            const qs = `level2_days=${Number(params.level2_days) || 15}&level3_days=${Number(params.level3_days) || 30}&cooldown_days=${Number(params.cooldown_days) || 3}`
            const res = await fetch(`${API_BASE_URL}/automations/fee-reminders/run?${qs}`, { method: "POST", headers })
            if (res.ok) { setResult(await res.json()); void loadHistory() }
            else setError((await res.json().catch(() => ({}))).detail || "—")
        } finally {
            setRunning(false)
        }
    }

    const runDigest = async () => {
        if (!headers) return
        setDigestRunning(true); setError(null); setDigestResult(null)
        try {
            const qs = `days=${Number(digestParams.days) || 7}&grade_alert_threshold=${Number(digestParams.grade_alert_threshold) || 10}&absence_alert_count=${Number(digestParams.absence_alert_count) || 3}`
            const res = await fetch(`${API_BASE_URL}/automations/parent-digest/run?${qs}`, { method: "POST", headers })
            if (res.ok) { setDigestResult(await res.json()); void loadDigestHistory() }
            else setError((await res.json().catch(() => ({}))).detail || "—")
        } finally {
            setDigestRunning(false)
        }
    }

    const runFollowup = async () => {
        if (!headers) return
        setFollowupRunning(true); setError(null); setFollowupResult(null)
        try {
            const res = await fetch(`${API_BASE_URL}/automations/absence-followup/run?days=${Number(followupDays) || 2}`, { method: "POST", headers })
            if (res.ok) { setFollowupResult(await res.json()); void loadEventHistory("absence.followup", setFollowupHistory) }
            else setError((await res.json().catch(() => ({}))).detail || "—")
        } finally {
            setFollowupRunning(false)
        }
    }

    const runAnomaly = async () => {
        if (!headers) return
        setAnomalyRunning(true); setError(null); setAnomalyResult(null)
        try {
            const qs = `days=${Number(anomalyParams.days) || 7}&unpaid_threshold=${(Number(anomalyParams.unpaid_threshold) || 30) / 100}`
            const res = await fetch(`${API_BASE_URL}/automations/anomaly-digest/run?${qs}`, { method: "POST", headers })
            if (res.ok) { setAnomalyResult(await res.json()); void loadEventHistory("anomaly.digest", setAnomalyHistory) }
            else setError((await res.json().catch(() => ({}))).detail || "—")
        } finally {
            setAnomalyRunning(false)
        }
    }

    const eventBadge = (eventType: string) => {
        const isAlert = eventType.startsWith("parent.alert")
        return (
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${isAlert ? "bg-red-100 text-red-800" : "bg-emerald-100 text-emerald-800"}`}>
                {isAlert ? t("digestAlertBadge") : t("digestBadge")}
            </span>
        )
    }

    const levelBadge = (level: number) => (
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${level === 3 ? "bg-red-100 text-red-800" : level === 2 ? "bg-amber-100 text-amber-800" : "bg-blue-100 text-blue-800"}`}>N{level}</span>
    )

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><BellRing className="h-4 w-4" /> {t("feeReminders")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("feeRemindersHint")}</p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-3 md:grid-cols-4">
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("level2Days")}
                            <input type="number" min={1} value={params.level2_days} onChange={e => setParams({ ...params, level2_days: e.target.value })} className="apple-input mt-1 w-full" />
                        </label>
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("level3Days")}
                            <input type="number" min={2} value={params.level3_days} onChange={e => setParams({ ...params, level3_days: e.target.value })} className="apple-input mt-1 w-full" />
                        </label>
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("cooldownDays")}
                            <input type="number" min={1} value={params.cooldown_days} onChange={e => setParams({ ...params, cooldown_days: e.target.value })} className="apple-input mt-1 w-full" />
                        </label>
                        <div className="flex items-end">
                            <Button onClick={run} disabled={running} className="w-full bg-black text-white hover:bg-black/90">
                                {running ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                                {running ? t("running") : t("runNow")}
                            </Button>
                        </div>
                    </div>

                    {result && (
                        <div className="grid gap-3 rounded-xl border border-[#CCFBF1] bg-[#F0FDFA] p-4 text-sm dark:border-[#134E4A] dark:bg-[#0f1f1d] sm:grid-cols-5">
                            <div><p className="text-2xl font-bold text-[#0F766E]">{result.scanned}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("resultScanned")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{result.reminded}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("resultReminded")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{result.escalated}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("resultEscalated")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{result.sms_queued}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("resultSms")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{result.skipped_cooldown + result.skipped_not_due + result.skipped_paid}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("resultSkipped")}</p></div>
                        </div>
                    )}

                    <p className="text-xs text-[#94A3B8]">{t("cronHint")}</p>

                    <div>
                        <p className="mb-2 text-sm font-semibold text-[#111827] dark:text-white">{t("history")}</p>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("student")}</th><th className="px-3 py-2">{t("fee")}</th><th className="px-3 py-2">{t("levelCol")}</th><th className="px-3 py-2">{t("outstanding")}</th><th className="px-3 py-2">{t("channels")}</th><th className="px-3 py-2">{t("date")}</th></tr></thead>
                                <tbody>
                                    {history.length === 0 ? <tr><td colSpan={6} className="px-3 py-6 text-center text-[#6B7280]">{t("noHistory")}</td></tr> : history.map(r => (
                                        <tr key={r.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                            <td className="px-3 py-2 font-medium">{r.student_name || "—"}</td>
                                            <td className="px-3 py-2">{r.fee_title || `#${r.fee_id}`}</td>
                                            <td className="px-3 py-2">{levelBadge(r.level)}</td>
                                            <td className="px-3 py-2">{r.outstanding_amount.toLocaleString()} FCFA</td>
                                            <td className="px-3 py-2">{r.channels.join(", ")}</td>
                                            <td className="px-3 py-2">{new Date(r.created_at).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><Mail className="h-4 w-4" /> {t("parentDigest")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("parentDigestHint")}</p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-3 md:grid-cols-4">
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("digestDays")}
                            <input type="number" min={1} max={31} value={digestParams.days} onChange={e => setDigestParams({ ...digestParams, days: e.target.value })} className="apple-input mt-1 w-full" />
                        </label>
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("digestGradeThreshold")}
                            <input type="number" min={0} max={20} value={digestParams.grade_alert_threshold} onChange={e => setDigestParams({ ...digestParams, grade_alert_threshold: e.target.value })} className="apple-input mt-1 w-full" />
                        </label>
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("digestAbsenceCount")}
                            <input type="number" min={1} max={31} value={digestParams.absence_alert_count} onChange={e => setDigestParams({ ...digestParams, absence_alert_count: e.target.value })} className="apple-input mt-1 w-full" />
                        </label>
                        <div className="flex items-end">
                            <Button onClick={runDigest} disabled={digestRunning} className="w-full bg-black text-white hover:bg-black/90">
                                {digestRunning ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                                {digestRunning ? t("running") : t("runNow")}
                            </Button>
                        </div>
                    </div>

                    {digestResult && (
                        <div className="grid gap-3 rounded-xl border border-[#CCFBF1] bg-[#F0FDFA] p-4 text-sm dark:border-[#134E4A] dark:bg-[#0f1f1d] sm:grid-cols-5">
                            <div><p className="text-2xl font-bold text-[#0F766E]">{digestResult.links}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("digestLinks")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{digestResult.digests}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("digestSent")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{digestResult.grade_alerts}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("digestGradeAlerts")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{digestResult.absence_alerts}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("digestAbsenceAlerts")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{digestResult.skipped_cooldown}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("resultSkipped")}</p></div>
                        </div>
                    )}

                    <p className="text-xs text-[#94A3B8]">{t("digestCronHint")}</p>

                    <div>
                        <p className="mb-2 text-sm font-semibold text-[#111827] dark:text-white">{t("history")}</p>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("digestType")}</th><th className="px-3 py-2">{t("digestRecipient")}</th><th className="px-3 py-2">{t("digestSubject")}</th><th className="px-3 py-2">{t("date")}</th></tr></thead>
                                <tbody>
                                    {digestHistory.length === 0 ? <tr><td colSpan={4} className="px-3 py-6 text-center text-[#6B7280]">{t("noHistory")}</td></tr> : digestHistory.map(n => (
                                        <tr key={n.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                            <td className="px-3 py-2">{eventBadge(n.event_type)}</td>
                                            <td className="px-3 py-2 font-medium">{n.recipient_name || "—"}</td>
                                            <td className="px-3 py-2" title={n.message}>{n.subject || "—"}</td>
                                            <td className="px-3 py-2">{new Date(n.created_at).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><UserX className="h-4 w-4" /> {t("absenceFollowup")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("absenceFollowupHint")}</p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-3 md:grid-cols-4">
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("followupDays")}
                            <input type="number" min={1} max={31} value={followupDays} onChange={e => setFollowupDays(e.target.value)} className="apple-input mt-1 w-full" />
                        </label>
                        <div className="flex items-end md:col-start-4">
                            <Button onClick={runFollowup} disabled={followupRunning} className="w-full bg-black text-white hover:bg-black/90">
                                {followupRunning ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                                {followupRunning ? t("running") : t("runNow")}
                            </Button>
                        </div>
                    </div>

                    {followupResult && (
                        <div className="grid gap-3 rounded-xl border border-[#CCFBF1] bg-[#F0FDFA] p-4 text-sm dark:border-[#134E4A] dark:bg-[#0f1f1d] sm:grid-cols-4">
                            <div><p className="text-2xl font-bold text-[#0F766E]">{followupResult.scanned}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("resultScanned")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{followupResult.notified}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("followupNotified")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{followupResult.sms_queued}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("resultSms")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{followupResult.skipped_done + followupResult.skipped_no_contact}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("resultSkipped")}</p></div>
                        </div>
                    )}

                    <p className="text-xs text-[#94A3B8]">{t("followupCronHint")}</p>

                    <div>
                        <p className="mb-2 text-sm font-semibold text-[#111827] dark:text-white">{t("history")}</p>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("digestRecipient")}</th><th className="px-3 py-2">{t("digestSubject")}</th><th className="px-3 py-2">{t("date")}</th></tr></thead>
                                <tbody>
                                    {followupHistory.length === 0 ? <tr><td colSpan={3} className="px-3 py-6 text-center text-[#6B7280]">{t("noHistory")}</td></tr> : followupHistory.map(n => (
                                        <tr key={n.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                            <td className="px-3 py-2 font-medium">{n.recipient_name || "—"}</td>
                                            <td className="px-3 py-2" title={n.message}>{n.subject || "—"}</td>
                                            <td className="px-3 py-2">{new Date(n.created_at).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><AlertTriangle className="h-4 w-4" /> {t("anomalyDigest")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("anomalyDigestHint")}</p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-3 md:grid-cols-4">
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("digestDays")}
                            <input type="number" min={1} max={31} value={anomalyParams.days} onChange={e => setAnomalyParams({ ...anomalyParams, days: e.target.value })} className="apple-input mt-1 w-full" />
                        </label>
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("anomalyUnpaidThreshold")}
                            <input type="number" min={0} max={100} value={anomalyParams.unpaid_threshold} onChange={e => setAnomalyParams({ ...anomalyParams, unpaid_threshold: e.target.value })} className="apple-input mt-1 w-full" />
                        </label>
                        <div className="flex items-end md:col-start-4">
                            <Button onClick={runAnomaly} disabled={anomalyRunning} className="w-full bg-black text-white hover:bg-black/90">
                                {anomalyRunning ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                                {anomalyRunning ? t("running") : t("runNow")}
                            </Button>
                        </div>
                    </div>

                    {anomalyResult && (anomalyResult.skipped_cooldown ? (
                        <div className="rounded-xl border border-[#FDE68A] bg-[#FFFBEB] px-3 py-2 text-sm text-[#92400E] dark:border-[#78350F] dark:bg-[#2d2410] dark:text-[#fcd34d]">{t("anomalyCooldown")}</div>
                    ) : (
                        <div className="grid gap-3 rounded-xl border border-[#CCFBF1] bg-[#F0FDFA] p-4 text-sm dark:border-[#134E4A] dark:bg-[#0f1f1d] sm:grid-cols-4">
                            <div><p className="text-2xl font-bold text-[#0F766E]">{anomalyResult.anomalies}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("anomalyCount")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{anomalyResult.absences_current ?? 0}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("anomalyAbsences")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{Math.round((anomalyResult.unpaid_ratio ?? 0) * 100)}%</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("anomalyUnpaid")}</p></div>
                            <div><p className="text-2xl font-bold text-[#0F766E]">{anomalyResult.class_size_min ?? 0}–{anomalyResult.class_size_max ?? 0}</p><p className="text-[#134E4A] dark:text-[#5eead4]">{t("anomalyClassSizes")}</p></div>
                        </div>
                    ))}

                    <p className="text-xs text-[#94A3B8]">{t("anomalyCronHint")}</p>

                    <div>
                        <p className="mb-2 text-sm font-semibold text-[#111827] dark:text-white">{t("history")}</p>
                        <div className="space-y-2">
                            {anomalyHistory.length === 0 ? <p className="px-3 py-4 text-center text-sm text-[#6B7280]">{t("noHistory")}</p> : anomalyHistory.map(n => (
                                <details key={n.id} className="rounded-xl border border-[#E5E7EB] px-3 py-2 dark:border-[#3b4248]">
                                    <summary className="cursor-pointer text-sm font-medium text-[#111827] dark:text-white">{n.subject || "—"} <span className="ml-2 text-xs font-normal text-[#6B7280]">{new Date(n.created_at).toLocaleString()}</span></summary>
                                    <pre className="mt-2 whitespace-pre-wrap font-sans text-sm text-[#374151] dark:text-[#c7d0da]">{n.message}</pre>
                                </details>
                            ))}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
