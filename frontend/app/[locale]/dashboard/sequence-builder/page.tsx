"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useLocale, useTranslations } from "next-intl"
import { BookOpenText, RefreshCw, Sparkles } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface Pair { class_id: number; class_name: string; level?: string | null; subject_id: number; subject_name: string; weekly_slots: number; weekly_minutes: number }
interface TermOption { id: number; name: string; start_date?: string | null; end_date?: string | null }
interface SequenceResult { class_name: string; subject_name: string; term_name: string; weekly_slots: number; weekly_minutes: number; weeks: number; sessions: number; sequence: string }

export default function SequenceBuilderPage() {
    const t = useTranslations("sequenceBuilder")
    const locale = useLocale()
    const { token } = useAuth()
    const [pairs, setPairs] = useState<Pair[]>([])
    const [terms, setTerms] = useState<TermOption[]>([])
    const [pairKey, setPairKey] = useState("")
    const [termId, setTermId] = useState("")
    const [topic, setTopic] = useState("")
    const [busy, setBusy] = useState(false)
    const [result, setResult] = useState<SequenceResult | null>(null)
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/automations/sequence/options`, { headers })
        if (res.ok) {
            const data = await res.json()
            setPairs(data.pairs || [])
            setTerms(data.terms || [])
            if (data.pairs?.length) setPairKey(`${data.pairs[0].class_id}-${data.pairs[0].subject_id}`)
            if (data.terms?.length) setTermId(String(data.terms[0].id))
        }
    }, [headers])

    useEffect(() => { void load() }, [load])

    const selected = pairs.find(p => `${p.class_id}-${p.subject_id}` === pairKey)

    const run = async () => {
        if (!headers || !selected || !termId) return
        setBusy(true); setError(null); setResult(null)
        try {
            const qs = `class_id=${selected.class_id}&subject_id=${selected.subject_id}&term_id=${termId}&language=${locale}&topic=${encodeURIComponent(topic)}`
            const res = await fetch(`${API_BASE_URL}/automations/sequence/run?${qs}`, { method: "POST", headers })
            if (res.ok) setResult(await res.json())
            else setError((await res.json().catch(() => ({}))).detail || "—")
        } finally {
            setBusy(false)
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
                    <CardTitle className="flex items-center gap-2"><BookOpenText className="h-4 w-4" /> {t("parameters")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("parametersHint")}</p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-3 md:grid-cols-4">
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("pair")}
                            <select value={pairKey} onChange={e => setPairKey(e.target.value)} className="apple-select mt-1 w-full">
                                {pairs.length === 0 && <option value="">{t("noPairs")}</option>}
                                {pairs.map(p => (
                                    <option key={`${p.class_id}-${p.subject_id}`} value={`${p.class_id}-${p.subject_id}`}>
                                        {p.class_name} — {p.subject_name}
                                    </option>
                                ))}
                            </select>
                        </label>
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("term")}
                            <select value={termId} onChange={e => setTermId(e.target.value)} className="apple-select mt-1 w-full">
                                {terms.length === 0 && <option value="">{t("noTerms")}</option>}
                                {terms.map(term => <option key={term.id} value={term.id}>{term.name}</option>)}
                            </select>
                        </label>
                        <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("topic")}
                            <input value={topic} onChange={e => setTopic(e.target.value)} placeholder={t("topicPlaceholder")} className="apple-input mt-1 w-full" />
                        </label>
                        <div className="flex items-end">
                            <Button onClick={run} disabled={busy || !selected || !termId} className="w-full bg-black text-white hover:bg-black/90">
                                {busy ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
                                {t("generate")}
                            </Button>
                        </div>
                    </div>
                    {selected && (
                        <p className="text-xs text-[#94A3B8]">{t("slotsInfo", { slots: selected.weekly_slots, minutes: selected.weekly_minutes })}</p>
                    )}
                    <p className="text-xs text-[#94A3B8]">{t("creditsHint")}</p>
                </CardContent>
            </Card>

            {result && (
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader>
                        <CardTitle>{result.subject_name} — {result.class_name} ({result.term_name})</CardTitle>
                        <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">
                            {t("resultStats", { slots: result.weekly_slots, weeks: result.weeks, sessions: result.sessions })}
                        </p>
                    </CardHeader>
                    <CardContent>
                        <pre className="whitespace-pre-wrap font-sans text-sm text-[#374151] dark:text-[#c7d0da]">{result.sequence}</pre>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
